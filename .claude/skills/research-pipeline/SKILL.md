---
name: research-pipeline
description: Run the research pipeline on a study folder from inside an interactive session, dispatching each step to its own subagent. Use when the user asks to run, resume, or rerun a study, or to run a specific step (study-guide, data, tags, analysis, grade).
---

# Research pipeline (interactive runner)

Arguments: `<study> [--from STEP] [--to STEP]`. `<study>` is a folder name under `studies/` or a path.

The headless equivalent is `pipeline/run.py run <study> [--from STEP] [--to STEP]`. Prefer the headless runner when the user is not in the session; use this skill when they want to watch or answer the designer's questions live.

## Steps

Read `pipeline/steps.toml`. It lists the steps in order with their agent, required inputs, outputs, and tools. Run `python3 pipeline/run.py status <study>` to see which outputs exist and which step is next.

## For each step from --from to --to

1. Confirm every required input exists in the study folder. If one is missing, stop and tell the user which step produced it.
2. If any output already exists, move it to `history/<YYYYmmdd-HHMMSS>-<step>/` inside the study folder.
3. Spawn the step's agent with the Agent tool, `subagent_type` set to the agent name from the manifest, `run_in_background: false`. Give it this prompt and nothing else from your context:

   ```
   Study folder: studies/<name>
   Step: <step name>

   Read docs/CONVENTIONS.md and your guidance file first, then do your step as defined in your agent instructions.
   Inputs you may read in the study folder: <inputs>.
   Outputs you must write: <outputs>.
   Do not read any other file in the study folder. Do not write status.json.
   When you finish, reply with one line stating which output files you wrote.
   ```

4. Check the outputs exist. For the `data`, `tags`, and `analysis` steps run the matching check:
   - `python3 pipeline/validate_csv.py --data <study>`
   - `python3 pipeline/validate_csv.py --tagged <study>`
   - `python3 pipeline/check_quotes.py <study>`
   If a check fails, stop and show the user its output.
5. Append a run entry to `status.json` in the study folder with step, agent, started, finished, status (`ok`, `failed`, `needs-input`), and outputs.

## When the study designer needs input

If the `study-guide` step ends without `10-study-guide.md` and `00-brief.md` now has an `## Open questions` section with empty `A:` lines, put those questions to the user with AskUserQuestion, write their answers into the `A:` lines, and rerun the step.

## Rules

- Never do a step's work yourself, and never pass one agent's reasoning to the next. The study folder is the only shared state.
- Never spawn the grader with anything from the analyst's transcript.
- Report at the end: which steps ran, which files they wrote, and the result of each check.
