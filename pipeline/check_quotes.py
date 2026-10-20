#!/usr/bin/env python3
"""Check that every quote in 40-analysis.md appears verbatim in the data.

A quote is text inside straight or curly double quotes, at least 20 characters
long. When the quote is followed by (Pnn), it must appear in that participant's
row; otherwise it must appear in some row. Matching ignores case, surrounding
punctuation, and whitespace differences. Trailing ellipses are allowed.

Usage: check_quotes.py <study-dir>
Exit 1 if any quote is not found.
"""

import csv
import re
import sys
from pathlib import Path

MIN_LEN = 20
QUOTE_RE = re.compile(r'["“](.+?)["”](?:\s*\((P\d+)\))?', re.S)


def norm(s):
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = s.replace("…", "...")
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s.strip(" .,;:!?'\"-")


def main():
    study = Path(sys.argv[1])
    analysis = (study / "40-analysis.md").read_text()
    data_file = study / "30-data-tagged.csv"
    if not data_file.exists():
        data_file = study / "20-data.csv"
    with open(data_file, newline="") as f:
        rows = list(csv.reader(f))
    header, rows = rows[0], rows[1:]
    text_by_pid = {r[0]: norm(" | ".join(r[1:])) for r in rows}
    all_text = "\n".join(text_by_pid.values())

    quotes = [(q, pid) for q, pid in QUOTE_RE.findall(analysis) if len(q.strip()) >= MIN_LEN]
    missing = []
    for q, pid in quotes:
        n = norm(q)
        # allow "..." elisions: every fragment must appear, in order, in the same row
        fragments = [norm(x) for x in re.split(r"\.\.\.|…|\[\.\.\.\]", n) if norm(x)]
        haystack = text_by_pid.get(pid) if pid else all_text
        if pid and haystack is None:
            missing.append((q, pid, "unknown participant"))
            continue
        pos = 0
        ok = True
        for frag in fragments:
            i = haystack.find(frag, pos)
            if i < 0:
                ok = False
                break
            pos = i + len(frag)
        if not ok:
            missing.append((q, pid, "not found" + (f" in {pid}'s row" if pid else " in any row")))

    attributed = sum(1 for _, pid in quotes if pid)
    if missing:
        print(f"40-analysis.md: {len(missing)} of {len(quotes)} quotes not found in {data_file.name}")
        for q, pid, why in missing:
            print(f" - {why}: \"{q[:80]}{'...' if len(q) > 80 else ''}\"")
        sys.exit(1)
    print(f"40-analysis.md: ok ({len(quotes)} quotes verified, {attributed} attributed to a participant)")
    if quotes and attributed < len(quotes):
        print(f"  note: {len(quotes) - attributed} quote(s) have no (Pnn) attribution")


if __name__ == "__main__":
    main()
