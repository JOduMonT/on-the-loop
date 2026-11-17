"""Write INDEX.md: one pointer line per doc, newest first.

  python -I <skill>/assets/index.py [repo]   # default: current folder

Each line: last git sync (date, commit), tokens it cost, path, one-line summary.
Summary and tokens come from the file's front matter (`summary:`, `tokens:`),
so a reader or an agent scans the index instead of opening every file.
Time and commit come from git, never typed by hand.
"""
import sys, re, pathlib, subprocess, yaml

repo = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
git = lambda *a: subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=True).stdout.strip()

rows = []
for p in sorted(repo.rglob("*.md")):
    rel = p.relative_to(repo).as_posix()
    if rel.startswith(".") or rel == "INDEX.md":
        continue
    text = p.read_text(encoding="utf-8")
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?(.*)$", text, re.S)
    try:
        meta = (yaml.safe_load(m.group(1)) or {}) if m else {}
    except yaml.YAMLError:
        meta = {"summary": "BAD HEADER: fix the front matter (quote values that contain a colon)"}
    body = m.group(2) if m else text
    summary = meta.get("summary") or next((l.strip("# ").strip() for l in body.splitlines() if l.strip()), "")
    tokens = meta.get("tokens")
    if isinstance(tokens, dict):
        tokens = tokens.get("total")
    when = git("log", "-1", "--format=%cs %h", "--", rel) or "unsynced"
    rows.append((when, tokens if tokens is not None else "—", rel, summary[:120]))

rows.sort(key=lambda r: r[0], reverse=True)
out = ["# Index", "", f"Generated from git at {git('rev-parse', '--short', 'HEAD')}. Do not edit by hand.", "",
       "| Synced (date, commit) | Tokens | File | Summary |", "|---|---|---|---|"]
out += [f"| {w} | {t} | [{r}]({r}) | {s} |" for w, t, r, s in rows]
(repo / "INDEX.md").write_text("\n".join(out) + "\n", encoding="utf-8")
print(f"INDEX.md: {len(rows)} files")
