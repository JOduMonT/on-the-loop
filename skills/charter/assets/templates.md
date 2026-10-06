# Templates

## Setup options (fill with the repo's real answers)
| Option | Adds | Effort | Score (estimate) | Risk |
|---|---|---|---|---|
| Minimal | Operating core in `AGENTS.md`, `wiki/log.md` | ~15 min | | Little structure for preferences |
| Standard (usual recommendation) | + settings cascade, decision records, pinned references and init, drift check | ~1 h | | More files to maintain |
| Full | + iteration plans and retrospectives, page templates, optional provider adapters | ~half a day | | Easy to over-build; apply "lean" |

## Install record in `AGENTS.md` (makes remove exact; see `references/setup.md`)
```
<!-- charter:begin v1.4 | created: <paths of files the setup created> -->
(Operating core, verbatim from assets/operating-core.md)
Full text: [charter](<path>/references/charter.md).
<!-- charter:end -->
```

## Reply shape (time is the constraint)
- **Now:** the one thing only the human can do, and why it unlocks the rest.
- **Next:** one line.
- **Later:** one line, with its trigger.

## Purpose and goal (in `AGENTS.md`)
- **Purpose** (optional; one sentence, a direction, never "done"; owner-approved, dated):
- **Short form** (15 words or fewer, for daily use):
- **Highest goal** (project, cycle, epic, sprint or story) (SMART: Specific, Measurable, Affect, Reasonable and relevant, Time-bound):
- **Definition of Done** (the 20 % that yields 80 % of the value):
- **Clean-goal check:** energises you? serves the Purpose? no hidden competing goal? no open objection?

## Delegation brief
- **Goal:**
- **Limits** (tools, repos, data it may touch):
- **Definition of Done:**
- **Expected value** (MoSCoW, % estimate):
- **Time box** (planned; record the actual in the log entry):
- **Attempts** (maximum tries, then stop and report):
- **Exit** (owner says stop: halt and report in one reply; self-stop if something outside the brief needs the owner):
- **Reviewer:**

## Log entries (OKF `log.md`: date headings newest first, entries added at the top of the date)
```
## YYYY-MM-DD
* **Delegation**: <agent/role> handed "<goal>" (expected Must 85 %); returned: accepted | revised | rejected, actual value <...>.
* **Decision**: <title> (Should 75 %). <one or two sentences: what, why, what is deferred>.
```

## Cycle gate (end of each cycle)
- Goal and Definition of Done reached? continue / stop / change.
- Any progress counts as on track. None: energy test, then troubleshoot. Slipping back: keep going.
- Objections logged since the last gate: answered, or turned into decisions?

## Signal check (owner tests agent, or reviewer tests delegate)
- Answers allowed: yes · no · rephrase · not now · don't know.
- Warm-up: two questions with known answers. Reset each session.
- Agree-with-me test: known answer, opposite expectation stated. Follows the expectation: recalibrate.

## Operating-core drift (pulse question)
"Is this still the right way of working for you? What would you change?"
