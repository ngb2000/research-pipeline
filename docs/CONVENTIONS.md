# Conventions

Every agent reads this file before doing its step. It defines the study folder, the file names, and the format of each artifact. Agents read only the inputs their step names and write only the outputs their step names.

## Study folder

One study per folder under `studies/`, named `<YYYY-MM-DD>-<slug>`. Files inside carry a two-digit prefix for the step that wrote them. The runner decides what has run by which files exist.

| Prefix | File | Written by | Reads |
|---|---|---|---|
| 00 | `00-brief.md` | human or `/new-study` | nothing |
| 10 | `10-study-guide.md` | study-designer | 00 |
| 20 | `20-data.csv`, `20-ground-truth.md` | data-generator | 10 |
| 30 | `30-data-tagged.csv`, `30-codebook.md` | tagger | 10, 20-data.csv |
| 40 | `40-analysis.md` | analyst | 10, 30 |
| 50 | `50-grade.md` | grader | 10, 20-ground-truth.md, 30, 40 |

`status.json` is the runner's log. Agents never write it. `history/<timestamp>/` holds outputs that a rerun replaced.

`20-ground-truth.md` is the answer key for synthetic studies. The tagger and analyst must not open it. Real studies have no ground-truth file.

## Identifiers

- Participants: `P01`, `P02`, ... zero-padded to two digits (three digits above 99).
- Questions: `Q01`, `Q02`, ... assigned in the study guide and never renumbered.
- Research questions: `RQ1`, `RQ2`, ...
- Tags: `group:value`, lowercase, hyphens inside values. Examples: `channel:in-person`, `sentiment:negative`, `blocker:id-verification`. Several tags in one cell are separated by `; `.

## 00-brief.md

```markdown
# Brief: <title>

## Objective
<one paragraph>

## Audience
<who the participants are>

## Research questions
RQ1. ...
RQ2. ...

## Constraints
<optional: method, participant count, timeline, anything fixed in advance>

## Open questions
<written by the study designer when the brief is missing something; see below>
```

If the study designer cannot write the study guide from the brief, it appends an `## Open questions` section and stops without writing `10-study-guide.md`:

```markdown
## Open questions
1. Q: Should the questionnaire cover web users, or only the app?
   A:
```

A human fills in each `A:` and reruns. An empty `A:` counts as unanswered.

## 10-study-guide.md

```markdown
# Study guide: <title>

**Method:** structured-interview | survey
**Participants:** 24

## Objective
## Audience
## Research questions
RQ1. ...

## Participant criteria
### Must have
- ...
### Must not have
- ...
### Segments
| Column | Values | Target |
|---|---|---|
| channel | app; web; in-person | 8 each |

## Questionnaire
| ID | Question | Type | Options | RQ |
|---|---|---|---|---|
| Q01 | How did you first hear about ...? | free-text | | RQ1 |
| Q02 | How satisfied were you with ...? | likert-5 | 1=Very dissatisfied; 5=Very satisfied | RQ2 |
| Q03 | Which channel did you use? | single-choice | app; web; in-person | RQ1 |
| Q04 | How many days did it take? | numeric | | RQ2 |

## Anticipated tags
### channel
- `channel:app` — opened the account in the mobile app
### sentiment
- `sentiment:negative` — ...
```

Question types: `free-text`, `likert-N` (N = scale size), `single-choice`, `multi-choice`, `numeric`. Only `free-text` columns get tagged. Segment columns become CSV columns. The questionnaire table and the `**Participants:**` line are parsed by scripts, so keep their format exact.

## 20-data.csv

One row per participant. Columns in order: `participant_id`, each segment column, then one column per question with the header `Qnn. <question text>`. Multi-choice answers are separated by `; `. Blank cells are allowed and mean no answer.

## 20-ground-truth.md

```markdown
# Ground truth

## Personas
| participant_id | persona | segment summary |

## Planted patterns
1. **<pattern>** — expected in N of M participants in <segment>. RQ: RQ1. Expected tags: `blocker:id-verification`.

## Noise
- P07: off-topic answer to Q03.
- Blank cells: P03 Q05, P11 Q02.
```

## 30-data-tagged.csv

`20-data.csv` with a `Qnn_tags` column inserted immediately after each free-text question column. Original cells are unchanged.

## 30-codebook.md

```markdown
# Codebook

| Tag | Group | Definition | Source | Count | Rationale |
|---|---|---|---|---|---|
| channel:app | channel | ... | guide | 8 | |
| blocker:photo-id | blocker | ... | tagger | 5 | 5 answers describe failed ID photo capture; no guide tag covers it |

## Tagging notes
<ambiguities, borderline calls, tags from the guide that were never used>
```

Source is `guide` or `tagger`.

## 40-analysis.md

```markdown
# Analysis: <title>

## Summary
<what was studied and the top-line finding, then key findings as bullets ordered by importance>

## RQ1. <research question>
### <header that states the finding>
<finding with counts from the tag columns>
> "verbatim quote" (P12)

## Limitations
## Next steps
```

Quotes are verbatim from the data, in double quotes, followed by the participant ID in parentheses. Every count names the tag or column it came from.

## 50-grade.md

```markdown
# Grade

| Criterion | Score (0-5) | Notes |
|---|---|---|
| Quote fidelity | | |
| Count fidelity | | |
| Recall of planted patterns | | |
| Fabrication | | |
| Coverage | | |
| Tag quality | | |

## Planted patterns
| Pattern | Result (recovered / missed / contradicted) | Where |

## Defects
## Suggested guidance updates
### <agent>
- ...
```

## Guidance documents

`guidance/<agent>.md` holds rules learned from graded runs. Each agent reads its own file before working. Humans edit these files; agents never do.
