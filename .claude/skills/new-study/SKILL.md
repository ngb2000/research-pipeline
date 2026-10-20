---
name: new-study
description: Create a study folder with a 00-brief.md from the user's research objective, audience, and research questions. Use when the user wants to start a new study, survey, or interview analysis.
---

# New study

Arguments: an optional slug, and whatever the user said about the study.

1. Collect the objective, the audience, and the research questions. If the user's message has all three, do not ask. If any is missing, ask for the missing ones in a single question. Do not ask about participant count, method, or segments; the study designer decides those or asks later through the brief.
2. Choose a folder name `studies/<YYYY-MM-DD>-<slug>`, the slug being three to five lowercase hyphenated words describing the topic. Use the user's slug if they gave one. Today's date is in your context.
3. Write `00-brief.md` in the format in `docs/CONVENTIONS.md`: title, Objective, Audience, Research questions numbered `RQ1.`..., and Constraints for anything the user fixed in advance (method, count, deadline). Leave out the Open questions section.
4. Tell the user the folder path and how to start the pipeline: `python3 pipeline/run.py run <folder>` or `/research-pipeline <folder>`.
