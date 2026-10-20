# research-pipeline

Analyzes survey and structured-interview data in five isolated steps. Each step runs as a separate agent with a fresh context, reads only files in the study folder, and writes one numbered output. No agent evaluates its own work.

| Step | Agent | Reads | Writes |
|---|---|---|---|
| study-guide | study-designer | `00-brief.md` | `10-study-guide.md` |
| data | data-generator | `10-study-guide.md` | `20-data.csv`, `20-ground-truth.md` |
| tags | tagger | 10, `20-data.csv` | `30-data-tagged.csv`, `30-codebook.md` |
| analysis | analyst | 10, 30 | `40-analysis.md` |
| grade | grader | 10, 30, 40, `20-ground-truth.md` | `50-grade.md` |

## Quick start

```bash
# 1. Write a brief (or use /new-study in Claude Code)
mkdir studies/2026-10-21-my-study && $EDITOR studies/2026-10-21-my-study/00-brief.md

# 2. Run every step headless
pipeline/run.py run 2026-10-21-my-study

# 3. Or run part of it
pipeline/run.py run 2026-10-21-my-study --from tags --to analysis
pipeline/run.py status 2026-10-21-my-study
pipeline/run.py check 2026-10-21-my-study
```

The runner invokes `claude -p --agent <name>` for each step, moves any previous outputs to `history/`, runs the deterministic checks, and logs to `status.json`. If the study designer needs more information it appends open questions to `00-brief.md` and the runner stops; answer them in the file and rerun.

Inside an interactive Claude Code session, `/research-pipeline <study>` does the same with subagents and relays the designer's questions to you.

## Layout

```
.claude/agents/      one definition per step agent
.claude/skills/      new-study, research-pipeline (interactive entry points)
pipeline/            steps.toml, run.py, validate_csv.py, check_quotes.py
guidance/            per-agent rules learned from graded runs (human-edited)
docs/                PLAN.md, CONVENTIONS.md
studies/<date>-<slug>/   one folder per study
```

`docs/CONVENTIONS.md` defines every file format. `docs/PLAN.md` has the design and phases.
