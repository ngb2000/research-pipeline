"""Parse the machine-readable parts of 10-study-guide.md. Shared by the check scripts."""

import re

QUESTION_TYPES = {"free-text", "single-choice", "multi-choice", "numeric"}


def parse_table(text, header_first_cell):
    """Return rows (as lists of cell strings) of the markdown table whose first header cell matches."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells and cells[0] == header_first_cell and i + 1 < len(lines) and set(lines[i + 1].strip()) <= set("|-: "):
            rows = []
            for row in lines[i + 2:]:
                if not row.strip().startswith("|"):
                    break
                rows.append([c.strip() for c in row.strip().strip("|").split("|")])
            return cells, rows
    return None, []


def parse_study_guide(text):
    m = re.search(r"\*\*Participants:\*\*\s*(\d+)", text)
    participants = int(m.group(1)) if m else None

    header, rows = parse_table(text, "ID")
    questions = []
    for r in rows:
        if len(r) < 3:
            continue
        questions.append({"id": r[0].strip("`"), "text": r[1], "type": r[2], "options": r[3] if len(r) > 3 else "", "rq": r[4] if len(r) > 4 else ""})

    _, seg_rows = parse_table(text, "Column")
    segments = [r[0].strip("`") for r in seg_rows if r and r[0]]

    return {"participants": participants, "questions": questions, "segments": segments}


def valid_type(t):
    return t in QUESTION_TYPES or re.fullmatch(r"likert-\d+", t) is not None
