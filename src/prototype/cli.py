"""Triage one incident from a ticket and its logs.

    python -m src.prototype.cli --ticket prototype/examples/results_approval/ticket.txt
                                --logs prototype/examples/results_approval/logs.txt
                                [--reader keyword|claude] [--ask] [--json report.json]

--reader keyword (the default) reads offline. --reader claude sends the redacted ticket and
logs to the Claude API; do not use it on real Directorate tickets without approval.
--ask asks you for any check the logs do not show; without it, such a check is unavailable.
"""
import argparse
import json
import os
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")      # silence TensorFlow's start-up messages

from src.prototype.reading import KeywordReader                 # noqa: E402
from src.prototype.triage import load_agent, operator_prompt, triage  # noqa: E402
from src.sim.scenario import load_scenario                      # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
PILOT = ROOT / "experiments" / "pilot"


def load_inputs(model_path=PILOT / "pilot_model.json", settings_path=PILOT / "pilot_settings.json",
                config_path=PILOT / "prototype_config.json"):
    model = json.loads(Path(model_path).read_text(encoding="utf-8"))
    config = json.loads(Path(config_path).read_text(encoding="utf-8"))
    return model, config, load_scenario(model_path, settings_path)


def make_reader(name, model, config, **kwargs):
    if name == "keyword":
        return KeywordReader(model, config)
    from src.prototype.llm import ClaudeReader
    return ClaudeReader(model, config, **kwargs)


def render(report, model):
    reading, decision = report["reading"], report["decision"]
    names = {x["id"]: x["name"] for group in ("symptoms", "context", "checks") for x in model[group]}
    out = [f"Read by: {reading['reader']}", f"Category: {reading['category']}", f"Summary: {reading['summary']}", ""]
    out.append("Symptoms")
    for key, f in reading["symptoms"].items():
        out.append(f"  {key} {names[key]}: {f['value']}" + (f"  <- {f['evidence']}" if f["evidence"] else ""))
    out.append("Context")
    for key, f in reading["context"].items():
        note = f"  <- {f['evidence']}" if f["source"] != "default" else "  (not stated; default)"
        out.append(f"  {names[key]}: {f['value']}{note}")
    for warning in reading["warnings"]:
        out.append(f"  Warning: {warning}")
    out += ["", "What the agent did"]
    for i, step in enumerate(report["steps"], 1):
        line = f"  {i}. {step['action']}"
        if "result" in step:
            line += f" -> {step['result']}"
            if step["evidence"]:
                line += f"  <- {step['evidence']}"
        if "blocked_by" in step:
            line += " -> BLOCKED by " + "; ".join(
                f"{b['rule']} (needs {b['needs']} first: {b['reason']})" for b in step["blocked_by"])
        out.append(line)
    out.append("")
    if decision["outcome"] == "recommended":
        out.append(f"RECOMMEND: {decision['remedy']}")
        out.append(f"  Likely cause: {decision['cause']} {decision['cause_name']}")
        out.append("  A recommendation only. A person applies the fix.")
    else:
        out.append("ESCALATE to a human expert")
        out.append(f"  Why: {decision['reason']}")
    out.append(f"  Checks run: {decision['checks_run']} (about {decision['check_minutes']} min), "
               f"blocked proposals: {decision['blocked_proposals']}")
    out += ["", "For the person who takes it next (calculated from the ratings; the agent does not see this):"]
    out += [f"  {r['cause']} {r['name']}: {r['probability']:.0%}" for r in report["reference"]]
    return "\n".join(out)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ticket", required=True, type=Path)
    parser.add_argument("--logs", type=Path, help="log file; omit if there are none")
    parser.add_argument("--reader", choices=["keyword", "claude"], default="keyword")
    parser.add_argument("--ask", action="store_true", help="ask for checks the logs do not show")
    parser.add_argument("--run", type=Path, help="trained agent run (default: agent_run in prototype_config.json)")
    parser.add_argument("--json", type=Path, help="also save the full report as JSON")
    args = parser.parse_args(argv)

    model, config, scenario = load_inputs()
    ticket = args.ticket.read_text(encoding="utf-8")
    logs = args.logs.read_text(encoding="utf-8") if args.logs else ""
    reading = make_reader(args.reader, model, config).read(ticket, logs)
    agent = load_agent(args.run or ROOT / config["agent_run"])
    report = triage(reading, scenario, model, agent, ask=operator_prompt() if args.ask else None)
    print(render(report, model))
    if args.json:
        args.json.write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
