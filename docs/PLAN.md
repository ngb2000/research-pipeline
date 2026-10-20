# Research pipeline: implementation plan

The pipeline analyzes survey or structured-interview data in five isolated steps. Each step runs as a separate agent with a fresh context, reads only files inside a study folder, and writes one numbered output file. The runner chains steps, and any step can be started on its own as long as its input files exist.

## Recommendation: subagents plus a runner, not a skill

Build this as a collection of **subagents** (one per step) with two thin **skills** as entry points and a **headless runner script**. Package it as a project now and convert it to a plugin once it stabilizes.

A single skill does not satisfy the requirements. A skill loads instructions into the calling session's context, so a tagger-as-skill would still see the test-writer's reasoning. Subagent definitions (`.claude/agents/*.md`) get their own context, their own tool allowlist, and their own model. Running them headless with `claude -p --agent <name>` gives the strongest isolation: each step is a separate process whose only shared state is the study folder on disk.

The two skills exist for convenience inside an interactive session:

- `/new-study` scaffolds a study folder from a prompt and writes `00-brief.md`.
- `/research-pipeline run <study> [--from <step>] [--to <step>]` dispatches steps to subagents in order. The dispatcher does no evaluation; it only checks that each expected output file appeared.

## Repository layout

```
research-pipeline/
  .claude/
    agents/
      study-designer.md          # step 1 (the "test-writer")
      data-generator.md          # step 2
      tagger.md                  # step 3
      analyst.md                 # step 4
      grader.md                  # step 5
    skills/
      new-study/SKILL.md
      research-pipeline/SKILL.md
  pipeline/
    steps.yaml                   # step order, agent, required inputs, outputs
    run.py                       # headless runner: loops over steps, calls claude -p
    check_quotes.py              # deterministic: every quote in analysis exists in data
    validate_csv.py              # deterministic: header matches study guide question IDs
  guidance/
    study-designer.md            # living guidance docs, one per agent
    data-generator.md
    tagger.md
    analyst.md
    grader.md
  studies/
    2026-10-20-onboarding-dropoff/
      00-brief.md
      10-study-guide.md
      20-data.csv
      20-ground-truth.md         # test runs only; hidden from tagger and analyst
      30-data-tagged.csv
      30-codebook.md
      40-analysis.md
      50-grade.md
      status.json
      history/                   # prior outputs, moved here before a step reruns
```

## File-naming convention

Every artifact carries a two-digit step prefix. The prefix states which step produced it, and the gap between numbers leaves room to insert steps later.

| Prefix | File | Written by | Required inputs |
|---|---|---|---|
| 00 | `00-brief.md` | human or `/new-study` | none |
| 10 | `10-study-guide.md` | study-designer | 00 |
| 20 | `20-data.csv`, `20-ground-truth.md` | data-generator (or ingest) | 10 |
| 30 | `30-data-tagged.csv`, `30-codebook.md` | tagger | 10, 20-data |
| 40 | `40-analysis.md` | analyst | 10, 30 |
| 50 | `50-grade.md` | grader | 10, 20-ground-truth, 30, 40 |

Rules that make "start from any step" work:

- **Output files are the state.** The runner decides what has run by which prefixed files exist. `status.json` is a log (step, agent, model, start, end, exit status), not the source of truth.
- **A step reads only lower-prefixed files** named in its agent definition. The agent prompt lists allowed inputs explicitly, and the ground-truth file is excluded from the tagger and analyst.
- **Reruns move, never overwrite.** Before a step runs, its previous outputs move to `history/<timestamp>/`.
- **Question IDs are stable.** The study guide assigns `Q01`, `Q02`, ... and the CSV header uses `Q01. <question text>`. Tag columns use the same ID: `Q01_tags`.
- **Tags are `group:value`.** Lowercase, hyphens inside values: `method:in-person`, `sentiment:negative`. The colon separates group from value unambiguously, which `method-in-person` does not. Multiple tags in a cell are separated by `;`.

## Step definitions

### 1. Study designer (the test-writer)

Input: `00-brief.md` with objective, audience, and research questions. Output: `10-study-guide.md` with those details plus participant count, participant criteria and segments, a questionnaire with question IDs and answer types (free text, Likert, single choice, numeric), and anticipated tags arranged in groups.

Missing information is handled on disk. If the brief lacks something the designer needs, it writes an **Open questions** section into `00-brief.md`, marks `status.json` as `needs-input`, and exits. The runner stops and reports. The human answers in the brief and reruns. In an interactive session the `/research-pipeline` skill relays the same questions through a prompt. Either way the designer never depends on chat context.

### 2. Data generator

Input: `10-study-guide.md`. Output: `20-data.csv` with one row per participant (`participant_id` = `P01`...) and one column per question, plus the segment columns from the participant criteria.

Also output `20-ground-truth.md`: the patterns the generator planted on purpose, with the counts it intended. Example: "6 of 20 in-person participants cite wait time as the top frustration; no app participants do." This file is the answer key for the grader and is the single biggest lever for making grades meaningful.

Generation rules that keep the data from being uniformly agreeable: assign each participant a hidden persona before writing any answers, vary answer length and literacy, include a few off-topic or contradictory answers, and leave a small share of cells blank.

### 3. Tagger

Inputs: `10-study-guide.md`, `20-data.csv`. Outputs: `30-data-tagged.csv` (original columns plus `Qnn_tags` columns) and `30-codebook.md` (every tag with its group, definition, count, and whether it came from the study guide or was added by the tagger, with a one-line rationale for each addition).

Work one question at a time across all participants rather than one participant at a time. Consistency within a question matters more than per-row speed, and it keeps batches small enough for large studies. Skip tagging for Likert, numeric, and single-choice columns; the analyst reads those directly.

### 4. Analyst

Inputs: `10-study-guide.md`, `30-data-tagged.csv`, `30-codebook.md`. Output: `40-analysis.md` organized by research question, each finding supported by counts from the tag columns and verbatim quotes with participant IDs.

Give the analyst permission to run a short script for counts. A language model counting tags across 40 rows is unreliable, and every number in the report should come from a computed tally. Quantitative columns get descriptive statistics by segment.

### 5. Grader (proposal to resolve the TBD)

Inputs: everything except the brief. Output: `50-grade.md` with a score and findings per step. Rubric:

- **Quote fidelity** (deterministic, `check_quotes.py`): every quoted string in the analysis appears verbatim in the data.
- **Count fidelity**: every number in the analysis matches a recount of the tagged data.
- **Recall of planted findings**: each pattern in `20-ground-truth.md` is recovered, missed, or contradicted.
- **Fabrication**: findings not supported by the data.
- **Coverage**: every research question answered; share of free-text cells left untagged.
- **Tag quality**: duplicated or overlapping tags, tags applied inconsistently to similar answers.

The grader writes a **Suggested guidance updates** section naming which agent's guidance doc should change and how. A human applies those changes. Keeping the guidance edits manual stops the pipeline from tuning itself toward whatever the grader happens to reward.

## Implementation phases

1. **Scaffold** (half a day): layout above, `steps.yaml`, `run.py` with status logging and history moves, empty guidance docs, one example brief.
2. **Design and generate**: study-designer and data-generator agents. Run one study to `20-data.csv` and read the data by hand before building anything downstream. Weak synthetic data makes every later grade meaningless.
3. **Tag and analyze**: tagger and analyst agents plus `validate_csv.py` and `check_quotes.py`.
4. **Grade**: grader agent and ground-truth comparison. Run the full pipeline on three example studies: one qualitative interview, one quantitative survey, one mixed.
5. **Refine**: update guidance docs from grades, rerun from step 3 on the same data, and compare `history/` against the new output. Add Google Sheets sync and real-data ingest here.

## Suggestions for improvement

- **Keep CSV canonical and treat Google Sheets as a mirror.** A Sheet is external state the pipeline cannot restart from without network access, and it does not diff in git. Add `--sheets` to the runner to push `20-data.csv` and `30-data-tagged.csv` after those steps and pull a Sheet into `20-data.csv` for real studies. The Google Drive connector in this workspace can do both.
- **Add an ingest path for real data.** The purpose is real surveys, and the generator is only a test harness. An `ingest` alternative for step 2 maps a survey export onto the study guide's question IDs. The study designer also needs a mode that writes a study guide around an existing questionnaire instead of authoring one.
- **Rename the first two agents.** "Test-writer" and "test-data-generator" describe the testing use, and the same agent designs real studies. "Study designer" and "data generator" read correctly in both cases.
- **Pin a model per agent.** The generator can run on a smaller model; the analyst and grader should run on the strongest available. Record the model in `status.json` so grades are comparable across runs.
- **Keep the tag set bounded.** The tagger should propose new tags only when an answer fits none of the existing ones, and cap additions per question. Unbounded tag growth is the most common way automated coding drifts.
- **Test the grader against bad analyses on purpose.** Feed it an analysis with a fabricated quote and a wrong count, and confirm it catches both before trusting its scores.
- **Minimum of 5 participants** for any study guide, and a default of 20 to 30 for synthetic runs, so planted patterns have enough rows to show up as counts.

## Open decisions

These do not block the scaffold. Defaults are stated; change them if they are wrong.

- Google Sheets as mirror (default) or as the canonical artifact.
- Real-data ingest in the first build (default: phase 5).
- Headless runner first (default) or the in-session skill first. Both use the same agent definitions.
