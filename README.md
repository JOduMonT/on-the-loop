# on-the-loop

A self-contained, provider-agnostic **charter** for working with an AI agent, packaged as an [Agent Skill](https://agentskills.io).

The human sets the limits; the agent acts inside them, reports, and stops at one-way doors: the human is **on the loop**.

## What it gives you
1. **Scored decisions, not debates.** MoSCoW (Must ≥ 80 %, Should 70–79, Could 60–69, Won't < 60) and a Pareto Definition of Done.
2. **A Level 5 chief of staff.** The agent anticipates, chooses a mental model, does the work within your limits, delegates with a brief, earns autonomy, and brings the next decision already scored.
3. **Every preference recorded at the right level** (a settings cascade: invariant → system → account → group → item → release).
4. **Drift check and re-setup.** At each retrospective the agent reads `index.md` and `log.md`, and suggests re-running the setup when the fit degrades. You decide.

It builds on two public references, fetched once and pinned by hash: the [LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) pattern and the [Open Knowledge Format](https://github.com/GoogleCloudPlatform/open-knowledge-format) (v0.2).

## Where it fits
Common ways to think about the layers of an agent system, and what this charter covers (it is about governance, not about building the machinery):

| Layer | Covered here? |
|---|---|
| Prompt: role, constraints, definition of done, output shape | Yes. The Operating core states them once, permanently, in `AGENTS.md`. |
| Context: what the model sees, in what order | Partly. Always-on core, on-demand skill, index first. No overflow rules. |
| Harness: tools, permissions, retries, traces | No. That belongs to your agent tool; the charter stays provider-agnostic. |
| Loop: run, check, correct, repeat | Yes, at human pace. Plan, implement, validate; retrospective; drift check; a maximum number of attempts per delegation. |
| Graph: who runs in parallel, who waits, where the human sits | Lightly. Roles (scout, builder, reviewer), the human on the loop, one-way doors. |

What the charter adds on top: scored decisions (MoSCoW, Pareto), a settings cascade so preferences persist, earned autonomy, and a re-setup process.

## How it loads
- **Permanent:** the setup writes a short *Operating core* into your repo's `AGENTS.md`, which agents read every session. The behaviour never depends on the skill being triggered.
- **On demand:** the `charter` skill runs the interactive setup and re-setup: it evaluates the repo, asks one round of questions, proposes 2–3 scored setups, and applies the one you pick.

## Install
Copy `skills/charter/` (a real folder, no symlinks) to where your agent looks for skills:
- the cross-client convention: `<repo>/.agents/skills/charter/` (or `~/.agents/skills/charter/` for all your projects);
- Claude Code: `<repo>/.claude/skills/charter/` (Claude Code does not scan `.agents/skills/`);
- other tools: see their skills documentation ([client list](https://agentskills.io/clients)).

Then tell your agent: **"apply the charter"**. Works on a new or an existing repository (it merges, never overwrites).

## Repository layout
```
skills/charter/
  SKILL.md                  # the procedure (loaded on demand)
  references/charter.md     # the full charter (canonical text)
  assets/operating-core.md  # the always-on block written into AGENTS.md
  assets/templates.md       # setup options, delegation brief, log entries
evals/trigger-queries.json  # 20 labelled prompts to test when the skill triggers
```

## Testing the description
`evals/trigger-queries.json` holds 10 prompts that should trigger the skill and 10 near-misses that should not, split 12 train / 8 validation, following [Optimizing skill descriptions](https://agentskills.io/skill-creation/optimizing-descriptions). Run each prompt about 3 times with your agent and check whether it loaded the skill.

## Licence
MIT. See [LICENSE](LICENSE).
