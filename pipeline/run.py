#!/usr/bin/env python3
"""Headless runner for the research pipeline.

Each step runs as a separate `claude -p --agent <name>` process. The only state
shared between steps is the study folder. Output files are the source of truth
for what has run; status.json is a log.

Usage:
  pipeline/run.py steps
  pipeline/run.py status <study-dir>
  pipeline/run.py run <study-dir> [--from STEP] [--to STEP] [--model MODEL] [--dry-run]
  pipeline/run.py check <study-dir>        # deterministic checks only, no agents
"""

import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "pipeline" / "steps.toml"
OPEN_QUESTIONS_HEADER = "## Open questions"


def load_steps():
    with open(MANIFEST, "rb") as f:
        return tomllib.load(f)["steps"]


def step_index(steps, name):
    for i, s in enumerate(steps):
        if s["name"] == name:
            return i
    names = ", ".join(s["name"] for s in steps)
    sys.exit(f"Unknown step '{name}'. Steps: {names}")


def now():
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def stamp():
    return dt.datetime.now().strftime("%Y%m%d-%H%M%S")


def load_status(study):
    p = study / "status.json"
    if p.exists():
        return json.loads(p.read_text())
    return {"runs": []}


def save_status(study, status):
    (study / "status.json").write_text(json.dumps(status, indent=2) + "\n")


def log_run(study, entry):
    status = load_status(study)
    status["runs"].append(entry)
    save_status(study, status)


def missing_inputs(study, step):
    return [f for f in step["inputs"] if not (study / f).exists()]


def archive_outputs(study, step, dry_run):
    existing = [f for f in step["outputs"] if (study / f).exists()]
    if not existing:
        return None
    dest = study / "history" / f"{stamp()}-{step['name']}"
    print(f"  moving previous outputs to {dest.relative_to(ROOT)}: {', '.join(existing)}")
    if not dry_run:
        dest.mkdir(parents=True, exist_ok=True)
        for f in existing:
            shutil.move(str(study / f), str(dest / f))
    return dest


def unanswered_questions(study):
    """True if 00-brief.md has an Open questions section with an empty A: line."""
    brief = study / "00-brief.md"
    if not brief.exists():
        return False
    text = brief.read_text()
    if OPEN_QUESTIONS_HEADER not in text:
        return False
    section = text.split(OPEN_QUESTIONS_HEADER, 1)[1]
    for line in section.splitlines():
        if line.strip().startswith("A:") and line.strip() == "A:":
            return True
    return False


def build_prompt(study, step):
    inputs = ", ".join(step["inputs"])
    optional = step.get("optional_inputs", [])
    outputs = ", ".join(step["outputs"])
    lines = [
        f"Study folder: {study.relative_to(ROOT)}",
        f"Step: {step['name']}",
        "",
        "Read docs/CONVENTIONS.md and your guidance file first, then do your step as "
        "defined in your agent instructions.",
        f"Inputs you may read in the study folder: {inputs}.",
    ]
    if optional:
        lines.append(f"Optional inputs, read if present: {', '.join(optional)}.")
    lines += [
        f"Outputs you must write: {outputs}.",
        "Do not read any other file in the study folder. Do not write status.json.",
        "When you finish, reply with one line stating which output files you wrote.",
    ]
    return "\n".join(lines)


def run_step(study, step, model, dry_run):
    name = step["name"]
    print(f"[{name}] agent={step['agent']}")
    missing = missing_inputs(study, step)
    if missing:
        sys.exit(f"  cannot start '{name}': missing inputs {missing}")

    archived = archive_outputs(study, step, dry_run)
    prompt = build_prompt(study, step)
    cmd = [
        "claude", "-p", "--agent", step["agent"],
        "--output-format", "json",
        "--allowedTools", *step.get("tools", []),
    ]
    model = model or step.get("model")
    if model:
        cmd += ["--model", model]
    if dry_run:
        print("  would run:", " ".join(cmd))
        print("  with prompt:\n    " + prompt.replace("\n", "\n    "))
        return True

    started = now()
    proc = subprocess.run(cmd, input=prompt, text=True, capture_output=True, cwd=ROOT)
    result = {}
    if proc.stdout.strip():
        try:
            result = json.loads(proc.stdout)
        except json.JSONDecodeError:
            result = {"raw": proc.stdout[-2000:]}

    produced = [f for f in step["outputs"] if (study / f).exists()]
    needs_input = name == "study-guide" and not produced and unanswered_questions(study)
    ok = proc.returncode == 0 and len(produced) == len(step["outputs"])

    entry = {
        "step": name,
        "agent": step["agent"],
        "model": model or next(iter(result.get("modelUsage") or {}), None),
        "started": started,
        "finished": now(),
        "exit_code": proc.returncode,
        "status": "needs-input" if needs_input else ("ok" if ok else "failed"),
        "outputs": produced,
        "archived_previous": str(archived.relative_to(ROOT)) if archived else None,
        "session_id": result.get("session_id"),
        "cost_usd": result.get("total_cost_usd"),
        "duration_ms": result.get("duration_ms"),
        "num_turns": result.get("num_turns"),
        "summary": (result.get("result") or "")[:500],
    }
    log_run(study, entry)

    if needs_input:
        print("  needs input: answer the Open questions in 00-brief.md and rerun.")
        return False
    if not ok:
        print(f"  failed (exit {proc.returncode}); produced {produced}")
        if proc.stderr.strip():
            print("  stderr:", proc.stderr.strip()[-2000:])
        if result.get("result"):
            print("  result:", str(result["result"])[-2000:])
        return False
    print(f"  ok: {', '.join(produced)}")
    return True


CHECKS = {
    "data": [("20-data.csv", ["validate_csv.py", "--data"])],
    "tags": [("30-data-tagged.csv", ["validate_csv.py", "--tagged"])],
    "analysis": [("40-analysis.md", ["check_quotes.py"])],
}


def run_checks(study, step_name=None):
    """Run deterministic checks. With step_name, only that step's checks; otherwise
    every check whose trigger file exists. Returns True if all pass."""
    ok = True
    groups = [CHECKS[step_name]] if step_name else CHECKS.values()
    for group in groups:
        for trigger, script in group:
            if not (study / trigger).exists():
                if step_name:
                    print(f"[check] skipped {script[0]}: {trigger} missing")
                continue
            cmd = [sys.executable, str(ROOT / "pipeline" / script[0]), *script[1:], str(study)]
            print(f"[check] {' '.join(script)}")
            proc = subprocess.run(cmd, text=True, capture_output=True)
            out = (proc.stdout + proc.stderr).strip()
            if out:
                print("  " + out.replace("\n", "\n  "))
            if proc.returncode != 0:
                ok = False
    return ok


def cmd_run(args):
    steps = load_steps()
    study = resolve_study(args.study)
    start = step_index(steps, args.from_step) if args.from_step else 0
    end = step_index(steps, args.to_step) if args.to_step else len(steps) - 1
    if start > end:
        sys.exit("--from comes after --to")
    for step in steps[start:end + 1]:
        if not run_step(study, step, args.model, args.dry_run):
            sys.exit(1)
        if not args.dry_run and not args.skip_checks and step["name"] in CHECKS:
            if not run_checks(study, step["name"]):
                print("  deterministic checks failed; stopping.")
                sys.exit(1)
    print("pipeline finished")


def cmd_status(args):
    steps = load_steps()
    study = resolve_study(args.study)
    print(f"study: {study.relative_to(ROOT)}")
    next_step = None
    for step in steps:
        have = [f for f in step["outputs"] if (study / f).exists()]
        state = "done" if len(have) == len(step["outputs"]) else ("partial" if have else "pending")
        if state != "done" and next_step is None and not missing_inputs(study, step):
            next_step = step["name"]
        print(f"  {step['name']:<12} {state:<8} {', '.join(step['outputs'])}")
    if unanswered_questions(study):
        print("  brief has unanswered open questions")
    print(f"next runnable step: {next_step or 'none'}")
    runs = load_status(study)["runs"]
    if runs:
        last = runs[-1]
        print(f"last run: {last['step']} {last['status']} at {last['finished']}")


def cmd_steps(args):
    for s in load_steps():
        print(f"{s['name']:<12} {s['agent']:<16} in={s['inputs']} out={s['outputs']}")


def cmd_check(args):
    study = resolve_study(args.study)
    sys.exit(0 if run_checks(study) else 1)


def resolve_study(arg):
    p = Path(arg)
    if not p.is_absolute():
        p = (ROOT / p) if (ROOT / p).exists() else (ROOT / "studies" / p)
    p = p.resolve()
    if not p.is_dir():
        sys.exit(f"study folder not found: {arg}")
    return p


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("steps", help="list steps").set_defaults(fn=cmd_steps)

    p = sub.add_parser("status", help="show which outputs exist")
    p.add_argument("study")
    p.set_defaults(fn=cmd_status)

    p = sub.add_parser("run", help="run steps in order")
    p.add_argument("study")
    p.add_argument("--from", dest="from_step")
    p.add_argument("--to", dest="to_step")
    p.add_argument("--model")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--skip-checks", action="store_true")
    p.set_defaults(fn=cmd_run)

    p = sub.add_parser("check", help="run deterministic checks on existing outputs")
    p.add_argument("study")
    p.set_defaults(fn=cmd_check)

    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
