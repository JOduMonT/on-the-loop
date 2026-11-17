# Components and token measure

Optional layer for a repo that wants its roles, gates, loops and rules as small composable files, and wants agent work measured. Skip it until plain prose files repeat themselves.

## One shape
One component per file in `components/`. Its `id` is its path without `.md`.

```yaml
---
id: agents/coordinator
kind: agent            # agent | seat | sidekick | skill | loop | gate | constraint | style | doc
version: 1
vars: [team.seats_max]                 # variables it reads, names only
uses: ["constraints/outbound-held"]    # other components, quoted ids
---
Body: only what the parts above do not already say. No templates in the body.
```

- A **gate set** is a gate that `uses:` other gates, so the number and order of gates is a list, not a rule.
- A **seat** is a role inside one team for one task (one commander plus workers). A **sidekick** (advisor, adversary, judge) attaches to a seat without changing it.

## Layers
`components/vars/defaults.yaml` (generic) ← `overlays/<name>/vars.yaml` (owner or business) ← the run.
- Variables merge like dicts, and the later layer wins.
- An overlay component `overlays/<name>/<id>.md` can **add** `uses:` and text, and never remove. A rule can be tightened, never widened.

## Tools
- `python -I assets/resolve.py lint`, run from the repo root, checks that ids match paths, kinds are known, references exist, there are no cycles, and there are no templates in bodies or vars (unset values are `null`).
- `python -I assets/resolve.py resolve <id> --overlay <name>` prints the flattened text: used components first, then the component, then overlay additions, then the merged variables and the repo commit.
- `python -I assets/index.py [repo]` writes `INDEX.md` with one line per note: last git sync (date, commit), `tokens:`, path, `summary:`. Agents read the index first and open only what they need.

## Order is cache order
Generic bodies come first and are the same for every owner, so a provider's prompt cache keeps them. Only the variables tail changes per owner or run.

## Token measure
- The unit is **tokens per verified result**, split into fresh input, cache read, cache write and output. Time and money are derived from it.
- A result is a verified deliverable, not a finished run.
- Each run record carries the repo commit it ran on.
- Watch three signals:
  - high cache writes, which mean cache misses (idle gaps, edits to instructions mid-session)
  - many calls per result, which means no batching
  - output with no result, which means wasted work
- Bulk reading goes to short-lived workers that return a summary. The coordinator's context stays small.
