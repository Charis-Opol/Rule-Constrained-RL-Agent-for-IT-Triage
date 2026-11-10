"""Phase 7 check of the prototype (extended 9 Nov 2026) on fictional cases.

1. Reading: how well each reader turns a ticket and its logs into the form, against the
   expected reading in cases.json: category, symptoms (present or not), context and the check
   results the reader fills in up front (positive, negative or not shown).
2. Reader error rates over all those check results, in the simulator's terms: how often a
   result the logs show is reversed (compare p_noise), how often it is missed (compare p_miss),
   and how often a result is read where the logs show none (not modelled in the simulator).
   The delegated check (D11) is scored separately, since only the delegate answers it.
3. Decision: what the agent, with the safety mechanism, does from each reader's form and from
   the expected form. The expected form separates reader errors from agent errors.

    python -m experiments.pilot.evaluate_prototype [--claude]
    python -m experiments.pilot.evaluate_prototype --cases prototype/examples/developer --out prototype_developer

--claude adds the Claude reader and delegate (needs Anthropic credentials; sends the cases only).
The researcher's cases show the pipeline works; they do not measure accuracy, because the same
person wrote the keywords and the cases. The developer's cases (Part 2 workbook) are the test.
"""
import argparse
import json
import os
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")

from src.prototype.cli import load_inputs, make_reader          # noqa: E402
from src.prototype.delegate import Delegation, make_delegate    # noqa: E402
from src.prototype.reading import (NOT_MENTIONED, NOT_SHOWN, PRESENT, Finding, Reading,  # noqa: E402
                                   apply_defaults)
from src.prototype.triage import load_agent, triage             # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "prototype" / "examples"
RESULTS = ROOT / "results" / "pilot"


def read_up_front(model):
    return [c for c in model["checks"] if not c.get("delegated")]


def expected_reading(expected, model, config):
    symptoms = {s["id"]: Finding(PRESENT if s["id"] in expected["symptoms_present"] else NOT_MENTIONED)
                for s in model["symptoms"]}
    context = {k: Finding(v, source="expected") for k, v in expected["context"].items()}
    checks = {c["id"]: Finding(expected["checks"].get(c["id"], NOT_SHOWN), source="expected")
              for c in model["checks"]}
    return apply_defaults(Reading("expected", expected["category"], "", symptoms, context, checks), model, config)


class ExpectedDelegate:
    """Answers a delegated check with the expected result, for the expected-form run."""
    name = "expected"

    def __init__(self, expected):
        self.expected = expected

    def analyse(self, check, ticket, logs):
        value = self.expected["checks"].get(check["id"], NOT_SHOWN)
        return Delegation(self.name, check["id"], "", Finding(value, source="expected"), "expected result")


def agreement(reading, expected, model):
    symptoms = [(reading.symptoms[s["id"]].value == PRESENT) == (s["id"] in expected["symptoms_present"])
                for s in model["symptoms"]]
    context = [reading.context[k].value == v for k, v in expected["context"].items()]
    checks = [reading.checks[c["id"]].value == expected["checks"].get(c["id"], NOT_SHOWN) for c in read_up_front(model)]
    return {"category": reading.category == expected["category"], "symptoms": [sum(symptoms), len(symptoms)],
            "context": [sum(context), len(context)], "checks": [sum(checks), len(checks)]}


def error_counts(pairs):
    """(expected, read) check results -> the counts behind the error rates."""
    shown = [(e, r) for e, r in pairs if e != NOT_SHOWN]
    hidden = [(e, r) for e, r in pairs if e == NOT_SHOWN]
    return {"shown": len(shown), "reversed": sum(r not in (e, NOT_SHOWN) for e, r in shown),
            "missed": sum(r == NOT_SHOWN for e, r in shown),
            "not_shown": len(hidden), "invented": sum(r != NOT_SHOWN for e, r in hidden)}


def rate(numerator, denominator):
    return f"{numerator}/{denominator} ({numerator / denominator:.0%})" if denominator else "-"


def describe(decision):
    failed = [a["cause"] for a in decision.get("attempts", []) if a["cleared"] is False]
    tried = f", after failed {'/'.join(failed)}" if failed else ""
    if decision["outcome"] == "fix":
        return f"fix {decision['cause']}" + (" (verified)" if decision.get("verified") else "") + tried
    if decision["outcome"] == "awaiting_verification":
        return f"fix {decision['cause']} (awaiting verification){tried}"
    return {"escalated": "escalate", "forced_escalation": "escalate (forced)", "step_limit": "escalate (step limit)",
            "fix_limit": "escalate (2 fixes failed)"}[decision["outcome"]] + tried


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--claude", action="store_true")
    parser.add_argument("--cases", type=Path, default=EXAMPLES, help="folder with cases.json and one folder per case")
    parser.add_argument("--out", default="prototype_v2",
                        help="results file name, without extension (prototype.md holds the Phase 7 run)")
    args = parser.parse_args(argv)

    model, config, scenario = load_inputs()
    agent = load_agent(ROOT / config["agent_run"])

    def verifier(name, case):
        """v3 agents: staging tests for code faults, otherwise the case's intended cause (demo only)."""
        if not scenario.verify:
            return None
        from src.prototype.verify import make_verifier
        return make_verifier(config["actions"], examples / name, intended=case["intended_cause"], demo=True)

    examples = args.cases.resolve()
    cases = json.loads((examples / "cases.json").read_text(encoding="utf-8"))["cases"]
    names = ["keyword"] + (["claude"] if args.claude else [])
    readers = {name: make_reader(name, model, config) for name in names}
    delegates = {"keyword": make_delegate("pattern", config)}
    if args.claude:
        delegates["claude"] = make_delegate("claude", config)
    delegated = [c for c in model["checks"] if c.get("delegated")]
    pairs = {name: [] for name in readers}
    delegate_pairs = {name: [] for name in readers}

    results = {}
    for name, case in cases.items():
        ticket = (examples / name / "ticket.txt").read_text(encoding="utf-8")
        logs_path = examples / name / "logs.txt"
        logs = logs_path.read_text(encoding="utf-8") if logs_path.exists() else ""
        expected = case["expected"]
        row = {"intended_cause": case["intended_cause"], "readers": {}}
        for reader_name, reader in readers.items():
            reading = reader.read(ticket, logs)
            report = triage(reading, scenario, model, agent, delegate=delegates[reader_name], ticket=ticket, logs=logs,
                            verify=verifier(name, case))
            row["readers"][reader_name] = {"agreement": agreement(reading, expected, model),
                                           "decision": report["decision"], "steps": report["steps"],
                                           "warnings": reading.warnings + report.get("warnings", [])}
            pairs[reader_name] += [(expected["checks"].get(c["id"], NOT_SHOWN), reading.checks[c["id"]].value)
                                   for c in read_up_front(model)]
            for check in delegated:      # asked directly, whether or not the agent chose it
                got = delegates[reader_name].analyse(check, ticket, logs).finding.value
                delegate_pairs[reader_name].append((expected["checks"].get(check["id"], NOT_SHOWN), got))
        report = triage(expected_reading(expected, model, config), scenario, model, agent,
                        delegate=ExpectedDelegate(expected), verify=verifier(name, case))
        row["readers"]["expected"] = {"decision": report["decision"], "steps": report["steps"]}
        results[name] = row

    errors = {name: {"reader": error_counts(pairs[name]), "delegate": error_counts(delegate_pairs[name])}
              for name in readers}
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / f"{args.out}.json").write_text(json.dumps({"agent_run": config["agent_run"], "model": config.get("model"),
                                                          "cases": results, "errors": errors}, indent=2),
                                              encoding="utf-8")

    where = examples.relative_to(ROOT).as_posix() if examples.is_relative_to(ROOT) else str(examples)
    lines = ["# Prototype check (Phase 7, extended 9 Nov 2026)", "",
             f"{len(cases)} fictional cases (`{where}`), model `{config.get('model')}`, agent `{config['agent_run']}` "
             "with the safety mechanism. This shows that the pipeline works; a handful of cases does not measure "
             "accuracy. Pilot data, not Directorate data.", "", "## Reading", "",
             "| Case | Reader | Category | Symptoms | Context | Checks |", "|---|---|---|---|---|---|"]
    for name, row in results.items():
        for reader_name in readers:
            a = row["readers"][reader_name]["agreement"]
            lines.append(f"| {name} | {reader_name} | {'yes' if a['category'] else 'no'} | "
                         f"{a['symptoms'][0]}/{a['symptoms'][1]} | {a['context'][0]}/{a['context'][1]} | "
                         f"{a['checks'][0]}/{a['checks'][1]} |")
    lines += ["", "## Reader error rates", "",
              "Over every check result in every case. Reversed: the logs show a result and the reader records the "
              "opposite (the simulator's p_noise). Missed: the logs show a result and the reader records none "
              "(p_miss). Invented: the logs show none and the reader records one (not modelled in the simulator). "
              "The delegate columns are the delegated check alone.", "",
              "| Reader | Reversed | Missed | Invented | Delegate reversed | Delegate missed | Delegate invented |",
              "|---|---|---|---|---|---|---|"]
    for name, e in errors.items():
        r, d = e["reader"], e["delegate"]
        lines.append(f"| {name} | {rate(r['reversed'], r['shown'])} | {rate(r['missed'], r['shown'])} | "
                     f"{rate(r['invented'], r['not_shown'])} | {rate(d['reversed'], d['shown'])} | "
                     f"{rate(d['missed'], d['shown'])} | {rate(d['invented'], d['not_shown'])} |")
    lines += ["", "## Decision", "",
              "Columns: the agent's decision from each reader's form, and from the expected form. "
              "Checks run and blocked proposals in brackets.", "",
              "| Case | Intended | " + " | ".join(list(readers) + ["expected"]) + " |",
              "|---|---|" + "---|" * (len(readers) + 1)]
    for name, row in results.items():
        cells = []
        for reader_name in list(readers) + ["expected"]:
            d = row["readers"][reader_name]["decision"]
            cells.append(f"{describe(d)} ({d['checks_run']} checks, {d['blocked_proposals']} blocked)")
        lines.append(f"| {name} | {row['intended_cause'] or 'none (escalate)'} | " + " | ".join(cells) + " |")
    (RESULTS / f"{args.out}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
