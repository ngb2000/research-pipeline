#!/usr/bin/env python3
"""Check 20-data.csv or 30-data-tagged.csv against 10-study-guide.md.

Usage: validate_csv.py (--data | --tagged) <study-dir>
Exit 1 on any problem.
"""

import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from studyguide import parse_study_guide, valid_type  # noqa: E402


def main():
    if len(sys.argv) != 3 or sys.argv[1] not in ("--data", "--tagged"):
        sys.exit(__doc__)
    tagged = sys.argv[1] == "--tagged"
    study = Path(sys.argv[2])
    guide = parse_study_guide((study / "10-study-guide.md").read_text())
    csv_path = study / ("30-data-tagged.csv" if tagged else "20-data.csv")
    problems = []

    if guide["participants"] is None:
        problems.append("study guide has no '**Participants:** N' line")
    if not guide["questions"]:
        problems.append("study guide has no questionnaire table starting with an 'ID' column")
    for q in guide["questions"]:
        if not re.fullmatch(r"Q\d{2,}", q["id"]):
            problems.append(f"bad question id {q['id']!r}")
        if not valid_type(q["type"]):
            problems.append(f"{q['id']}: unknown type {q['type']!r}")

    with open(csv_path, newline="") as f:
        reader = csv.reader(f)
        header = next(reader, [])
        rows = list(reader)

    if not header or header[0] != "participant_id":
        problems.append("first column must be participant_id")

    for seg in guide["segments"]:
        if seg not in header:
            problems.append(f"segment column {seg!r} missing")

    col_of = {}
    for q in guide["questions"]:
        matches = [i for i, h in enumerate(header) if h.startswith(q["id"] + ".") or h == q["id"]]
        if not matches:
            problems.append(f"column for {q['id']} missing")
            continue
        col_of[q["id"]] = matches[0]
        if tagged and q["type"] == "free-text":
            tag_col = q["id"] + "_tags"
            if tag_col not in header:
                problems.append(f"tag column {tag_col} missing")
            elif header.index(tag_col) != matches[0] + 1:
                problems.append(f"{tag_col} should directly follow the {q['id']} column")

    if guide["participants"] is not None and len(rows) != guide["participants"]:
        problems.append(f"study guide says {guide['participants']} participants, csv has {len(rows)} rows")

    ids = [r[0] for r in rows if r]
    if len(set(ids)) != len(ids):
        problems.append("duplicate participant_id values")
    for pid in ids:
        if not re.fullmatch(r"P\d{2,}", pid):
            problems.append(f"bad participant_id {pid!r}")
    for n, r in enumerate(rows, start=2):
        if len(r) != len(header):
            problems.append(f"line {n}: {len(r)} cells, header has {len(header)}")

    # Choice and likert answers must come from the options list.
    for q in guide["questions"]:
        i = col_of.get(q["id"])
        if i is None:
            continue
        if q["type"] in ("single-choice", "multi-choice") and q["options"]:
            allowed = {o.strip() for o in q["options"].split(";")}
            for r in rows:
                if i >= len(r) or not r[i].strip():
                    continue
                values = [v.strip() for v in r[i].split(";")] if q["type"] == "multi-choice" else [r[i].strip()]
                bad = [v for v in values if v not in allowed]
                if bad:
                    problems.append(f"{r[0]} {q['id']}: value(s) not in options: {bad}")
        if q["type"].startswith("likert-"):
            n = int(q["type"].split("-")[1])
            for r in rows:
                v = r[i].strip() if i < len(r) else ""
                if v and not (v.isdigit() and 1 <= int(v) <= n):
                    problems.append(f"{r[0]} {q['id']}: likert value {v!r} not in 1..{n}")
        if q["type"] == "numeric":
            for r in rows:
                v = r[i].strip() if i < len(r) else ""
                if v:
                    try:
                        float(v)
                    except ValueError:
                        problems.append(f"{r[0]} {q['id']}: numeric value {v!r} is not a number")

    if tagged:
        tag_re = re.compile(r"[a-z0-9]+:[a-z0-9-]+")
        for q in guide["questions"]:
            if q["type"] != "free-text" or q["id"] + "_tags" not in header:
                continue
            t = header.index(q["id"] + "_tags")
            a = col_of[q["id"]]
            for r in rows:
                if t >= len(r):
                    continue
                for tag in [x.strip() for x in r[t].split(";") if x.strip()]:
                    if not tag_re.fullmatch(tag):
                        problems.append(f"{r[0]} {q['id']}_tags: malformed tag {tag!r}")
                if r[t].strip() and not r[a].strip():
                    problems.append(f"{r[0]} {q['id']}: tags on an empty answer")

    if problems:
        print(f"{csv_path.name}: {len(problems)} problem(s)")
        for p in problems[:50]:
            print(" -", p)
        if len(problems) > 50:
            print(f" ... and {len(problems) - 50} more")
        sys.exit(1)
    n_q = len(guide["questions"])
    print(f"{csv_path.name}: ok ({len(rows)} participants, {n_q} questions{', tagged' if tagged else ''})")


if __name__ == "__main__":
    main()
