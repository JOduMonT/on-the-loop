#!/usr/bin/env python3
"""Engram atomizer: session logs, git diffs or notes -> atoms -> wiki/atoms/ + memory index.

    python .agents/ingest_session.py --recent                  # git commits since the last run
    python .agents/ingest_session.py --input notes/today.md    # a note (.md), diff (.diff/.patch) or session log (.jsonl)
    python .agents/ingest_session.py --git HEAD~3..HEAD        # an explicit commit range
    python .agents/ingest_session.py --recent --dry-run        # print the atoms, write nothing

Each run makes one atom note, wiki/atoms/YYYY-MM-DD-topic.md, with the three things worth
remembering: a one-sentence summary, the decisions taken, and the exact commands or fixes
that worked (plus errors, with their cause). The note is Markdown, so Git versions it; the
same atoms are embedded into .agents/memory.sqlite for `memory.py search`.

The cheap model pass is the one in memory.py (the command in MEMORY_ATOMIZE_CMD). Without it,
a regex pass pulls decisions, fenced commands and errors straight from the text, so the
pipeline still works offline. Run it from the repository root; notes go to ATOMS_DIR
(default wiki/atoms).

Safety: session logs are reduced to the human and assistant text turns (no tool payloads),
and everything is redacted for keys, tokens and private keys before it reaches the model,
the note or the index.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import memory  # noqa: E402

REPO = Path.cwd()
ATOM_DIR = REPO / os.environ.get("ATOMS_DIR", "wiki/atoms")
MAX_INPUT_CHARS = 24000  # what one model call reads; long logs keep head and tail
MAX_TURN_CHARS = 1800
NOISE = ("<system-reminder", "<session-context", "<wake", "<task-notification",
         "<local-command", "<command-name", "[SYSTEM NOTIFICATION", "<relay")


def run(*argv):
    return subprocess.run(argv, cwd=REPO, capture_output=True, text=True,
                          encoding="utf-8", errors="replace").stdout


def clip(text, limit=MAX_INPUT_CHARS):
    if len(text) <= limit:
        return text
    half = limit // 2
    return text[:half] + "\n[...]\n" + text[-half:]


# ---------------------------------------------------------------- readers

def read_session(path):
    """JSON-lines session log: keep only the text of user and assistant turns."""
    turns, stamp = [], None
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get("type") not in ("user", "assistant") or rec.get("isMeta"):
            continue
        msg = rec.get("message") or {}
        content = msg.get("content")
        parts = [content] if isinstance(content, str) else [
            b.get("text", "") for b in (content or []) if isinstance(b, dict) and b.get("type") == "text"]
        text = "\n".join(p for p in parts if p).strip()
        if text.startswith("<wake"):  # chat-bridge envelope: keep the spoken message only
            text = "\n".join(re.findall(r"<message[^>]*>(.*?)</message>", text, re.S)).strip()
        if not text or text.startswith(NOISE):
            continue
        turns.append(f"{rec['type'].upper()}: {text[:MAX_TURN_CHARS]}")
        stamp = rec.get("timestamp") or stamp
    when = None
    if stamp:
        try:
            when = datetime.fromisoformat(stamp.replace("Z", "+00:00")).timestamp()
        except ValueError:
            pass
    return "\n\n".join(turns), when


def read_git(rev_range=None, since=None):
    """Commit messages, file stats and a capped patch for a range or a time window."""
    args = ["git", "log", "--no-merges", "--date=short", "--format=%n== %h %ad %s%n%b", "--stat=100"]
    args += [rev_range] if rev_range else [f"--since={since}"]
    log = run(*args).strip()
    if not log:
        return "", None
    patch = run("git", "log", "--no-merges", "-p", "--unified=1", "--format=== %h %s",
                *([rev_range] if rev_range else [f"--since={since}"]),
                "--", ".", ":(exclude)*.lock", ":(exclude)*.sqlite")
    stamp = run("git", "log", "-1", "--format=%ct", *([rev_range] if rev_range else [])).strip()
    return f"{log}\n\n# PATCH (truncated)\n{patch[:9000]}", float(stamp) if stamp else None


def read_input(path):
    p = Path(path)
    if p.suffix == ".jsonl":
        return read_session(p)
    return p.read_text(encoding="utf-8", errors="replace"), p.stat().st_mtime


# ---------------------------------------------------------------- atomizing

DECISION_RE = re.compile(r"\b(decided|decision|chose|chosen|going with|we will|will use|switch(?:ed)? to|"
                         r"instead of|rejected|adopted|standardi[sz]e)\b", re.I)
ERROR_RE = re.compile(r"(Traceback|Error:|error:|ERROR|Exception|failed|FAILED|not found|denied|refused|timed out)")
CMD_RE = re.compile(r"^\s*(?:\$ |> |PS> )?((?:git|python3?|pip|npm|npx|node|docker|wsl|curl|sqlite3|make|"
                    r"gh|sed|grep|ssh|ansible)\b[^\n]{3,200})$")


def regex_atoms(text):
    """No-model fallback: pull a summary, decisions, commands and errors by pattern."""
    atoms, seen = [], set()
    text = text.split("# PATCH (truncated)")[0]  # code in a patch is not prose
    lines = [l.strip() for l in text.splitlines()]

    def push(cat, content):
        content = re.sub(r"\s+", " ", content).strip(" -*>|")
        if 12 <= len(content) <= 400 and (cat, content) not in seen:
            seen.add((cat, content))
            atoms.append({"category": cat, "content": content})

    subjects = re.findall(r"^== \w+ \S+ (.+)$", text, re.M)  # git log: the commit subjects
    for subj in subjects:
        if re.match(r"(fix|bug|hotfix|revert)\b", subj, re.I):
            push("fix", subj)
    summary = "; ".join(subjects[:3])
    summary = summary or next((l for l in lines if l.lower().startswith(("**tldr", "tl;dr", "**tl;dr", "summary:"))), "")
    summary = summary or next((l for l in lines if l and not l.startswith(("#", "---", "==", "```"))), "")
    push("summary", re.sub(r"^\*{0,2}(TL;?DR|Summary):?\*{0,2}\s*", "", summary, flags=re.I))
    in_fence = False
    for l in lines:
        if l.startswith("```"):
            in_fence = not in_fence
            continue
        if CMD_RE.match(l) and (in_fence or l.startswith(("$", ">", "PS>"))):
            push("fix", CMD_RE.match(l).group(1))
        elif ERROR_RE.search(l) and not l.startswith("#"):
            push("error", l)
        elif DECISION_RE.search(l) and not l.startswith("#"):
            push("decision", l)
    return atoms[:30]


def model_atoms(text, source):
    return memory.atomize(text, source)  # None when no atomize command is set or it fails


def slug(text, words=6):
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return "-".join(s.split("-")[:words]) or "session"


# ---------------------------------------------------------------- output

SECTIONS = (("decision", "Decisions"), ("fix", "Commands and fixes"), ("error", "Errors and causes"))


def write_note(atoms, topic, day, source_desc):
    ATOM_DIR.mkdir(parents=True, exist_ok=True)
    base = f"{day}-{topic}"
    path = ATOM_DIR / f"{base}.md"
    n = 2
    while path.exists():
        path = ATOM_DIR / f"{base}-{n}.md"
        n += 1
    summary = next((a["content"] for a in atoms if a["category"] == "summary"), topic.replace("-", " "))
    lines = ["---", f'title: "{summary[:80].rstrip(".")}"', "type: atom", "tags: [atom, memory]",
             "status: active", f"updated: {day}", f'source: "{source_desc}"', "---",
             f"# {summary[:80].rstrip('.')}", "", f"**Summary:** {summary}", ""]
    for cat, heading in SECTIONS:
        items = [a["content"] for a in atoms if a["category"] == cat]
        if items:
            lines += [f"## {heading}"] + [f"- {i}" for i in items] + [""]
    other = [a for a in atoms if a["category"] not in ("summary",) + tuple(c for c, _ in SECTIONS)]
    if other:
        lines += ["## Other"] + [f"- ({a['category']}) {a['content']}" for a in other] + [""]
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    return path


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Turn session logs, git diffs or notes into atoms.")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--recent", action="store_true", help="git commits since the last ingest (first run: 24 h)")
    src.add_argument("--input", help="a .md note, .diff/.patch file or .jsonl session log")
    src.add_argument("--git", metavar="RANGE", help="a commit range such as HEAD~3..HEAD")
    ap.add_argument("--topic", help="slug for the note name (default: from the summary)")
    ap.add_argument("--date", help="YYYY-MM-DD (default: today)")
    ap.add_argument("--no-model", action="store_true", help="skip the model pass, use patterns only")
    ap.add_argument("--dry-run", action="store_true", help="print the atoms, write and index nothing")
    args = ap.parse_args(argv)

    db = None if args.dry_run else memory.init_db()
    head = run("git", "rev-parse", "HEAD").strip()
    if args.recent:
        row = db.execute("SELECT value FROM meta WHERE key='last_ingest_commit'").fetchone() if db else None
        rng = f"{row[0]}..HEAD" if row and row[0] != head else None
        if row and row[0] == head:
            print("nothing new since the last ingest")
            return
        text, when = read_git(rng, None if rng else "24 hours ago")
        desc = f"git {rng}" if rng else "git, last 24 hours"
    elif args.git:
        text, when = read_git(args.git)
        desc = f"git {args.git}"
    else:
        text, when = read_input(args.input)
        desc = Path(args.input).as_posix()
    text = memory.redact(text).strip()
    if not text:
        print("nothing to ingest")
        return

    window = clip(text)
    atoms = None if args.no_model else model_atoms(window, desc)
    method = "model" if atoms else "patterns"
    atoms = atoms or regex_atoms(window)
    atoms = [{**a, "content": memory.redact(a["content"])} for a in atoms]
    if not atoms:
        print("no atoms found")
        return
    if args.dry_run:
        print(json.dumps(atoms, ensure_ascii=False, indent=2))
        return

    ts = when or time.time()
    day = args.date or datetime.fromtimestamp(ts, timezone.utc).astimezone().strftime("%Y-%m-%d")
    summary = next((a["content"] for a in atoms if a["category"] == "summary"), "")
    path = write_note(atoms, args.topic or slug(summary or desc), day, desc)
    rel = path.relative_to(REPO).as_posix()
    if args.date:
        ts = memory.parse_when(args.date)
    added, skipped = memory.add(atoms, rel, ts, db)
    if args.recent:
        db.execute("INSERT OR REPLACE INTO meta VALUES ('last_ingest_commit', ?)", (head,))
        db.commit()
    print(f"{rel}: {len(atoms)} atom(s) via {method}; indexed {added}, {skipped} already stored")


if __name__ == "__main__":
    main()
