"""Triage one incident from a ticket and its logs.

    python -m src.prototype.cli --ticket prototype/examples/results_approval/ticket.txt
                                --logs prototype/examples/results_approval/logs.txt
                                [--reader keyword|claude] [--ask] [--json report.json]
                                [--delegate pattern|claude|off] [--act --pr local|github|off --patcher pre-written|claude]

--reader keyword (the default) reads offline. --reader claude sends the redacted ticket and
logs to the Claude API; do not use it on real Directorate tickets without approval.
--ask asks you for any check the logs do not show; without it, such a check is unavailable.
--delegate answers delegated checks (D11, a full log analysis) when the agent asks for one:
"pattern" offline, "claude" with the Claude API. --act carries the decision out (actions.py):
a draft pull request for a code fault (--pr local: a branch in results/pilot/demo_repo; github:
the throwaway repository), otherwise a simulated fix order to the owner in results/pilot/outbox.
"""
import argparse
import json
import os
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")      # silence TensorFlow's start-up messages

from src.prototype.delegate import make_delegate                # noqa: E402
from src.prototype.reading import KeywordReader                 # noqa: E402
from src.prototype.triage import load_agent, operator_prompt, triage  # noqa: E402
from src.sim.scenario import load_scenario                      # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
PILOT = ROOT / "experiments" / "pilot"


def load_inputs(model_path=None, settings_path=None, config_path=PILOT / "prototype_config.json"):
    """The model and settings named in the prototype config, unless given."""
    config = json.loads(Path(config_path).read_text(encoding="utf-8"))
    model_path = Path(model_path or ROOT / config.get("model", "experiments/pilot/pilot_model.json"))
    settings_path = Path(settings_path or ROOT / config.get("settings", "experiments/pilot/pilot_settings.json"))
    model = json.loads(model_path.read_text(encoding="utf-8"))
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
            if "delegation" in step:
                line += f"\n       delegated analysis ({step['delegation']['delegate']}): {step['delegation']['report']}"
        if "blocked_by" in step:
            line += " -> BLOCKED by " + "; ".join(
                f"{b['rule']} (needs {b['needs']} first: {b['reason']})" for b in step["blocked_by"])
        out.append(line)
    out.append("")
    if decision["outcome"] == "fix":
        out.append(f"FIX: {decision['remedy']}")
        out.append(f"  Likely cause: {decision['cause']} {decision['cause_name']}")
        out.append("  Rule checker re-confirmed: " + ("yes" if decision.get("permitted") else "NO"))
    else:
        out.append("ESCALATE to a human expert")
        out.append(f"  Why: {decision['reason']}")
    for warning in report.get("warnings", []):
        out.append(f"  Warning: {warning}")
    out.append(f"  Checks run: {decision['checks_run']} (about {decision['check_minutes']} min), "
               f"blocked proposals: {decision['blocked_proposals']}")
    out += ["", "For the person who takes it next (calculated from the ratings; the agent does not see this):"]
    out += [f"  {r['cause']} {r['name']}: {r['probability']:.0%}" for r in report["reference"]]
    return "\n".join(out)


def render_action(action):
    out = ["", f"ACTION: {action['kind'].replace('_', ' ')} -> {action['owner']} ({action['routed_because']})"]
    if "pull_request" in action:
        pr = action["pull_request"]
        out.append(f"  Draft pull request: {pr['where']}")
        out.append(f"  Patch: {pr['patch']} (written by {pr['patch_source']}); tests: {pr['tests']}")
    if "refused" in action:
        out.append(f"  No pull request: {action['refused']}")
    out.append(f"  Message (simulated, not sent): {action['message']}")
    return "\n".join(out)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ticket", required=True, type=Path)
    parser.add_argument("--logs", type=Path, help="log file; omit if there are none")
    parser.add_argument("--reader", choices=["keyword", "claude"], default="keyword")
    parser.add_argument("--ask", action="store_true", help="ask for checks the logs do not show")
    parser.add_argument("--run", type=Path, help="trained agent run (default: agent_run in prototype_config.json)")
    parser.add_argument("--json", type=Path, help="also save the full report as JSON")
    parser.add_argument("--delegate", choices=["pattern", "claude", "off"], default="pattern",
                        help="who answers delegated checks (default: offline patterns)")
    parser.add_argument("--act", action="store_true", help="carry the decision out (draft PR, fix order, escalation)")
    parser.add_argument("--pr", choices=["local", "github", "off"], default="local")
    parser.add_argument("--patcher", choices=["pre-written", "claude"], default="pre-written")
    parser.add_argument("--incident", help="incident id for branches and messages (default: the ticket's folder)")
    args = parser.parse_args(argv)

    model, config, scenario = load_inputs()
    ticket = args.ticket.read_text(encoding="utf-8")
    logs = args.logs.read_text(encoding="utf-8") if args.logs else ""
    reading = make_reader(args.reader, model, config).read(ticket, logs)
    agent = load_agent(args.run or ROOT / config["agent_run"])
    delegate = None if args.delegate == "off" else make_delegate(args.delegate, config)
    report = triage(reading, scenario, model, agent, ask=operator_prompt() if args.ask else None,
                    delegate=delegate, ticket=ticket, logs=logs)
    print(render(report, model))
    if args.act:
        from src.prototype.actions import act
        incident = args.incident or args.ticket.resolve().parent.name
        report["action"] = act(report, model, config["actions"], incident, ticket, pr=args.pr, patcher=args.patcher)
        print(render_action(report["action"]))
    if args.json:
        args.json.write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
