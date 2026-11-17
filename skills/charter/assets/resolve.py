"""Lint and resolve brain components. Stdlib + PyYAML.

Run from the repo root:
  python -I <skill>/assets/resolve.py lint
  python -I <skill>/assets/resolve.py resolve <id> [--overlay <name>]

A component is components/<id>.md with YAML front matter. id == path without .md.
Variables: components/vars/defaults.yaml, merged with overlays/<name>/vars.yaml.
Resolve = used components first (depth-first, deduplicated), then the
component, then any overlay additions, then the merged vars as a tail block.
Stable text comes first, so the cached prefix is shared.
"""
import sys, re, pathlib, subprocess, yaml

ROOT = pathlib.Path.cwd()
CORE = ROOT / "components"
KINDS = {"agent", "seat", "sidekick", "skill", "loop", "gate", "constraint", "style", "doc"}


def load(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?(.*)$", text, re.S)
    if not m:
        return None, text
    return yaml.safe_load(m.group(1)) or {}, m.group(2).strip()


def components():
    out = {}
    for p in sorted(CORE.rglob("*.md")):
        meta, body = load(p)
        if meta is not None:
            out[p.relative_to(CORE).with_suffix("").as_posix()] = (meta, body, p)
    return out


def lint():
    comps, errors = components(), []
    for cid, (meta, body, p) in comps.items():
        where = p.relative_to(ROOT).as_posix()
        if meta.get("id") != cid:
            errors.append(f"{where}: id '{meta.get('id')}' must be '{cid}'")
        if meta.get("kind") not in KINDS:
            errors.append(f"{where}: kind '{meta.get('kind')}' not in {sorted(KINDS)}")
        for ref in meta.get("uses") or []:
            if ref not in comps:
                errors.append(f"{where}: uses missing component '{ref}'")
        if "{{" in body:
            errors.append(f"{where}: component bodies hold no {{{{vars}}}}; declare them in vars:")
    def visit(cid, stack):
        if cid in stack:
            errors.append("cycle: " + " -> ".join(stack + [cid]))
            return
        for ref in (comps.get(cid, ({}, "", None))[0].get("uses") or []):
            visit(ref, stack + [cid])
    for cid in comps:
        visit(cid, [])
    for vf in [f for f in [CORE / "vars/defaults.yaml", *ROOT.glob("overlays/*/vars.yaml")] if f.exists()]:
        if "{{" in vf.read_text(encoding="utf-8"):
            errors.append(f"{vf.relative_to(ROOT).as_posix()}: a value refers to a template; use null for unset")
    for e in sorted(set(errors)):
        print("ERROR", e)
    print(f"{len(comps)} components, {len(set(errors))} errors")
    return 1 if errors else 0


def merge(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        return {k: merge(a[k], b[k]) if k in a and k in b else b.get(k, a.get(k)) for k in {**a, **b}}
    return a if b is None else b


def resolve(cid, overlay=None):
    comps, seen, parts = components(), set(), []
    def walk(c):
        if c in seen:
            return
        seen.add(c)
        meta, body, _ = comps[c]
        for ref in meta.get("uses") or []:
            walk(ref)
        parts.append(f"<!-- {c} -->\n{body}")
    walk(cid)
    dv = CORE / "vars/defaults.yaml"
    vars_ = (yaml.safe_load(dv.read_text(encoding="utf-8")) or {}) if dv.exists() else {}
    if overlay:
        od = ROOT / "overlays" / overlay
        extra = od / f"{cid}.md"
        if extra.exists():  # overlays add, never remove
            meta, body = load(extra)
            for ref in (meta or {}).get("uses") or []:
                walk(ref)
            parts.append(f"<!-- overlay {overlay}/{cid} -->\n{body}")
        vf = od / "vars.yaml"
        if vf.exists():
            vars_ = merge(vars_, yaml.safe_load(vf.read_text(encoding="utf-8")) or {})
    git = lambda *a: subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=True).stdout.strip()
    vars_["brain_commit"] = git("rev-parse", "--short", "HEAD") + ("-dirty" if git("status", "--porcelain") else "")  # copy into every run record
    parts.append("## Context (variables)\n```yaml\n" + yaml.safe_dump(vars_, sort_keys=True) + "```")
    print("\n\n".join(parts))


if __name__ == "__main__":
    if sys.argv[1:2] == ["lint"]:
        sys.exit(lint())
    if sys.argv[1:2] == ["resolve"]:
        ov = sys.argv[sys.argv.index("--overlay") + 1] if "--overlay" in sys.argv else None
        resolve(sys.argv[2], ov)
    else:
        print(__doc__)
