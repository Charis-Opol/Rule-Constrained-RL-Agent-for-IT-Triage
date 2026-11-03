"""Phase 7 check of the prototype on the fictional cases in prototype/examples.

1. Reading: how well each reader turns a ticket and its logs into the form, against the
   researcher's own reading (cases.json): category, symptoms (present or not), context and
   check results (positive, negative or not shown).
2. Decision: what the agent, with the safety mechanism, does from each reader's form and from
   the researcher's expected form. The expected form separates reader errors from agent errors.

    python -m experiments.pilot.evaluate_prototype [--claude]

--claude adds the Claude reader (needs Anthropic credentials; sends the fictional cases only).
Writes results/pilot/prototype.json and results/pilot/prototype.md. Six cases written by the
researcher: this shows the pipeline works, it does not measure accuracy.
"""
import argparse
import json
import os
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")

from src.prototype.cli import load_inputs, make_reader          # noqa: E402
from src.prototype.reading import (NOT_MENTIONED, NOT_SHOWN, PRESENT, Finding, Reading,  # noqa: E402
                                   apply_defaults)
from src.prototype.triage import load_agent, triage             # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "prototype" / "examples"
RESULTS = ROOT / "results" / "pilot"


def expected_reading(expected, model, config):
    symptoms = {s["id"]: Finding(PRESENT if s["id"] in expected["symptoms_present"] else NOT_MENTIONED)
                for s in model["symptoms"]}
    context = {k: Finding(v, source="expected") for k, v in expected["context"].items()}
    checks = {c["id"]: Finding(expected["checks"].get(c["id"], NOT_SHOWN), source="expected")
              for c in model["checks"]}
    return apply_defaults(Reading("expected", expected["category"], "", symptoms, context, checks), model, config)


def agreement(reading, expected, model):
    symptoms = [(reading.symptoms[s["id"]].value == PRESENT) == (s["id"] in expected["symptoms_present"])
                for s in model["symptoms"]]
    context = [reading.context[k].value == v for k, v in expected["context"].items()]
    checks = [reading.checks[c["id"]].value == expected["checks"].get(c["id"], NOT_SHOWN) for c in model["checks"]]
    return {"category": reading.category == expected["category"], "symptoms": [sum(symptoms), len(symptoms)],
            "context": [sum(context), len(context)], "checks": [sum(checks), len(checks)]}


def describe(decision):
    if decision["outcome"] == "recommended":
        return f"recommend {decision['cause']}"
    return {"escalated": "escalate", "forced_escalation": "escalate (forced)",
            "step_limit": "escalate (step limit)"}[decision["outcome"]]


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--claude", action="store_true")
    args = parser.parse_args(argv)

    model, config, scenario = load_inputs()
    agent = load_agent(ROOT / config["agent_run"])
    cases = json.loads((EXAMPLES / "cases.json").read_text(encoding="utf-8"))["cases"]
    readers = ["keyword"] + (["claude"] if args.claude else [])
    readers = {name: make_reader(name, model, config) for name in readers}

    results = {}
    for name, case in cases.items():
        ticket = (EXAMPLES / name / "ticket.txt").read_text(encoding="utf-8")
        logs_path = EXAMPLES / name / "logs.txt"
        logs = logs_path.read_text(encoding="utf-8") if logs_path.exists() else ""
        row = {"intended_cause": case["intended_cause"], "readers": {}}
        for reader_name, reader in readers.items():
            reading = reader.read(ticket, logs)
            report = triage(reading, scenario, model, agent)
            row["readers"][reader_name] = {"agreement": agreement(reading, case["expected"], model),
                                           "decision": report["decision"], "steps": report["steps"],
                                           "warnings": reading.warnings}
        report = triage(expected_reading(case["expected"], model, config), scenario, model, agent)
        row["readers"]["expected"] = {"decision": report["decision"], "steps": report["steps"]}
        results[name] = row

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "prototype.json").write_text(json.dumps({"agent_run": config["agent_run"], "cases": results},
                                                       indent=2), encoding="utf-8")

    lines = ["# Prototype check (Phase 7)", "",
             f"Six fictional cases written by the researcher (`prototype/examples`), agent `{config['agent_run']}` "
             "with the safety mechanism. This shows that the pipeline works; six cases do not measure accuracy. "
             "Pilot data, not Directorate data.", "", "## Reading", "",
             "| Case | Reader | Category | Symptoms | Context | Checks |", "|---|---|---|---|---|---|"]
    for name, row in results.items():
        for reader_name in readers:
            a = row["readers"][reader_name]["agreement"]
            lines.append(f"| {name} | {reader_name} | {'yes' if a['category'] else 'no'} | "
                         f"{a['symptoms'][0]}/{a['symptoms'][1]} | {a['context'][0]}/{a['context'][1]} | "
                         f"{a['checks'][0]}/{a['checks'][1]} |")
    lines += ["", "## Decision", "",
              "Columns: the agent's decision from each reader's form, and from the researcher's expected form. "
              "Checks run and blocked proposals in brackets.", "",
              "| Case | Intended | " + " | ".join(list(readers) + ["expected"]) + " |",
              "|---|---|" + "---|" * (len(readers) + 1)]
    for name, row in results.items():
        cells = []
        for reader_name in list(readers) + ["expected"]:
            d = row["readers"][reader_name]["decision"]
            cells.append(f"{describe(d)} ({d['checks_run']} checks, {d['blocked_proposals']} blocked)")
        lines.append(f"| {name} | {row['intended_cause'] or 'none (escalate)'} | " + " | ".join(cells) + " |")
    (RESULTS / "prototype.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
