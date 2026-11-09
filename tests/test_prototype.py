"""Phase 7: the prototype reads tickets and logs into the scenario model's terms, runs the agent
on them through the unchanged safety mechanism, and never lets a prohibited fix through."""
import json
import types
from pathlib import Path

import numpy as np
import pytest

from src.prototype.llm import ClaudeReader, ReaderError, form_schema, redact
from src.prototype.reading import (NEGATIVE, NOT_MENTIONED, NOT_SHOWN, POSITIVE, PRESENT, Finding, KeywordReader,
                                   Reading, apply_defaults, read_check)
from src.prototype.triage import LiveTriageEnv, operator_prompt, triage
from src.sim.scenario import build_scenario
from src.sim.triage_env import TriageEnv

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "experiments" / "pilot"
EXAMPLES = ROOT / "prototype" / "examples"
MODEL = json.loads((PILOT / "pilot_model.json").read_text(encoding="utf-8"))
SETTINGS = json.loads((PILOT / "pilot_settings.json").read_text(encoding="utf-8"))
CONFIG = json.loads((PILOT / "prototype_config.json").read_text(encoding="utf-8"))
SCENARIO = build_scenario(MODEL, SETTINGS)
CASES = json.loads((EXAMPLES / "cases.json").read_text(encoding="utf-8"))["cases"]

N_CHECKS, ESCALATE = 10, 18
FIX_C01, FIX_C02, FIX_C04 = 10, 11, 13
D05 = 4


def case_text(name):
    logs = EXAMPLES / name / "logs.txt"
    return ((EXAMPLES / name / "ticket.txt").read_text(encoding="utf-8"),
            logs.read_text(encoding="utf-8") if logs.exists() else "")


def reading(checks=None, production="Yes", priority="Low", present=("S01",)):
    symptoms = {s["id"]: Finding(PRESENT if s["id"] in present else NOT_MENTIONED) for s in MODEL["symptoms"]}
    found = {c["id"]: Finding((checks or {}).get(c["id"], NOT_SHOWN), "line", "logs") for c in MODEL["checks"]}
    context = {"X01": Finding(production, source="ticket"), "X02": Finding(priority, source="ticket")}
    return apply_defaults(Reading("test", "unclear", "", symptoms, context, found), MODEL, CONFIG)


class Scripted:
    """A stand-in agent that prefers actions in a fixed order, skipping masked ones."""

    def __init__(self, order):
        self.order = order

    def q_values(self, obs_with_mask):
        mask = np.asarray(obs_with_mask)[-(ESCALATE + 1):] > 0.5
        q = np.full(ESCALATE + 1, -5.0)
        for rank, action in enumerate(self.order):
            q[action] = 10.0 - rank
        q[~mask] = -np.inf
        return q


# ----- Log and ticket reading ------------------------------------------------
def test_threshold_check_reads_positive_negative_and_not_shown():
    spec = CONFIG["checks"]["D05"]
    assert read_check(spec, ["db active_transactions=4 oldest_tx_age=412s"]).value == POSITIVE
    assert read_check(spec, ["db active_transactions=4 oldest_tx_age=58s"]).value == NEGATIVE
    assert read_check(spec, ["api GET /x 200 duration=0.1s"]).value == NOT_SHOWN


def test_median_cpu_ignores_one_spike():
    spec = CONFIG["checks"]["D04"]
    lines = ["node api-1 cpu=30%", "node api-2 cpu=95%", "node api-3 cpu=40%"]
    assert read_check(spec, lines).value == NEGATIVE


def test_release_older_than_a_day_counts_as_negative():
    spec = CONFIG["checks"]["D09"]
    old = ["2026-10-30T17:20:00Z INFO deploy release v1 deployed", "2026-11-02T09:00:00Z ERROR api GET / 500"]
    recent = ["2026-11-02T06:00:00Z INFO deploy release v2 deployed", "2026-11-02T09:00:00Z ERROR api GET / 500"]
    assert read_check(spec, old).value == NEGATIVE
    assert read_check(spec, recent).value == POSITIVE


@pytest.mark.parametrize("name", list(CASES))
def test_keyword_reader_matches_the_written_cases(name):
    """A regression guard, not evidence of accuracy: the keywords were written for these cases."""
    got = KeywordReader(MODEL, CONFIG).read(*case_text(name))
    expected = CASES[name]["expected"]
    assert {k for k, f in got.symptoms.items() if f.value == PRESENT} == set(expected["symptoms_present"])
    assert {k: f.value for k, f in got.context.items()} == expected["context"]
    read_up_front = {c["id"] for c in MODEL["checks"] if not c.get("delegated")}   # D11 is asked for later
    assert ({k: f.value for k, f in got.checks.items() if f.value != NOT_SHOWN}
            == {k: v for k, v in expected["checks"].items() if k in read_up_front})


def test_unstated_context_takes_the_stricter_default():
    got = KeywordReader(MODEL, CONFIG).read("The system is slow today.", "")
    assert got.context["X01"].value == "Yes" and got.context["X01"].source == "default"
    assert got.context["X02"].value == "High"


def test_every_finding_carries_its_evidence():
    got = KeywordReader(MODEL, CONFIG).read(*case_text("results_approval"))
    ticket, logs = case_text("results_approval")
    for finding in list(got.symptoms.values()) + list(got.checks.values()):
        if finding.value in (PRESENT, POSITIVE, NEGATIVE):
            assert finding.evidence and finding.evidence in ticket + logs


# ----- Live environment --------------------------------------------------------
def test_live_observation_matches_the_simulator_for_the_same_evidence():
    sim = TriageEnv(SCENARIO, p_noise=0.0, p_miss=0.0)
    sim.reset(seed=3)
    live = LiveTriageEnv(SCENARIO, lambda i: bool(sim.reported[i]))
    live.reset(options={"symptoms": sim.symptoms, "context": sim.context})
    assert np.array_equal(sim._obs(), live._obs())
    for check in (1, 4, 8):
        sim_obs, live_obs = sim.step(check)[0], live.step(check)[0]
        assert np.array_equal(sim_obs, live_obs)


def test_a_check_is_looked_up_only_when_the_agent_runs_it():
    asked = []
    live = LiveTriageEnv(SCENARIO, lambda i: asked.append(i) or True)
    live.reset(options={"symptoms": [True, False, False, False], "context": [0, 0]})
    live.step(2)
    assert asked == [2] and live.status[2] == TriageEnv.POSITIVE


def test_a_check_the_logs_do_not_show_is_unavailable():
    live = LiveTriageEnv(SCENARIO, lambda i: None)
    live.reset(options={"symptoms": [True, False, False, False], "context": [0, 0]})
    live.step(D05)
    assert live.status[D05] == TriageEnv.UNAVAILABLE and not live.observed(D05)


# ----- Safety mechanism on real incidents --------------------------------------
def test_two_prohibited_proposals_escalate_and_no_fix_executes():
    """In production, R01 forbids C02's fix until D05 and R05 forbids C01's until D01."""
    report = triage(reading(), SCENARIO, MODEL, Scripted([FIX_C02, FIX_C01, ESCALATE]))
    assert report["decision"]["outcome"] == "forced_escalation"
    assert [s["blocked_by"][0]["rule"] for s in report["steps"]] == ["R01", "R05"]


def test_observing_the_named_check_lifts_the_rule():
    report = triage(reading({"D05": POSITIVE}), SCENARIO, MODEL, Scripted([D05, FIX_C02]))
    assert report["decision"]["outcome"] == "fix" and report["decision"]["cause"] == "C02"
    assert report["steps"][0]["result"] == POSITIVE


def test_an_unavailable_named_check_does_not_lift_the_rule():
    report = triage(reading(), SCENARIO, MODEL, Scripted([D05, FIX_C02, FIX_C01, ESCALATE]))
    assert report["steps"][0]["result"] == "unavailable"
    assert report["decision"]["outcome"] == "forced_escalation"


def test_rules_do_not_apply_outside_their_context():
    report = triage(reading(production="No"), SCENARIO, MODEL, Scripted([FIX_C02]))
    assert report["decision"]["outcome"] == "fix" and report["decision"]["cause"] == "C02"


def test_the_operator_can_supply_a_check_the_logs_do_not_show():
    ask = operator_prompt(input_fn=lambda prompt: "p", output_fn=lambda text: None)
    report = triage(reading(), SCENARIO, MODEL, Scripted([D05, FIX_C02]), ask=ask)
    assert report["steps"][0]["result"] == POSITIVE and report["steps"][0]["source"] == "operator"
    assert report["decision"]["cause"] == "C02"


def test_an_unruled_fix_passes_straight_through():
    report = triage(reading(), SCENARIO, MODEL, Scripted([FIX_C04]))
    assert report["decision"]["cause"] == "C04" and report["decision"]["blocked_proposals"] == 0


# ----- Language-model reader -----------------------------------------------------
def test_redaction_removes_contact_details_addresses_and_secrets():
    text = "From jane.doe@example.ac.ug on 0772123456 at 10.0.4.17, token=abc123SECRET"
    out = redact(text)
    for secret in ("jane.doe@example.ac.ug", "0772123456", "10.0.4.17", "abc123SECRET"):
        assert secret not in out


def test_form_schema_is_strict_and_built_from_the_model():
    schema = form_schema(MODEL)

    def walk(node):
        if node.get("type") == "object":
            assert node["additionalProperties"] is False
            assert set(node["required"]) == set(node["properties"])
            for child in node["properties"].values():
                walk(child)
    walk(schema)
    assert set(schema["properties"]["checks"]["properties"]) == {c["id"] for c in MODEL["checks"]}
    assert schema["properties"]["context"]["properties"]["X02"]["properties"]["state"]["enum"] == \
        ["Low", "Medium", "High", "not_stated"]


def fake_client(form, stop_reason="end_turn"):
    sent = {}

    def create(**kwargs):
        sent.update(kwargs)
        block = types.SimpleNamespace(type="text", text=json.dumps(form))
        return types.SimpleNamespace(stop_reason=stop_reason, content=[block])
    return types.SimpleNamespace(beta=types.SimpleNamespace(messages=types.SimpleNamespace(create=create))), sent


def blank_form():
    item = {"state": NOT_SHOWN, "evidence": ""}
    return {"category": "Database", "summary": "Approvals fail",
            "symptoms": {s["id"]: {"state": NOT_MENTIONED, "evidence": ""} for s in MODEL["symptoms"]},
            "context": {a["id"]: {"state": "not_stated", "evidence": ""} for a in MODEL["context"]},
            "checks": {c["id"]: dict(item) for c in MODEL["checks"]}}


def test_claude_reader_keeps_quoted_findings_and_discards_invented_ones():
    ticket, logs = case_text("results_approval")
    form = blank_form()
    form["checks"]["D02"] = {"state": POSITIVE, "evidence": "lock wait timeout exceeded; try restarting transaction"}
    form["checks"]["D06"] = {"state": POSITIVE, "evidence": "Seq Scan on results_approval"}       # not in the logs
    form["context"]["X01"] = {"state": "Yes", "evidence": "This is on the live system"}
    client, sent = fake_client(form)
    got = ClaudeReader(MODEL, CONFIG, client=client).read(ticket, logs)
    assert got.checks["D02"].value == POSITIVE and got.checks["D02"].source == "logs"
    assert got.checks["D06"].value == NOT_SHOWN and any("D06" in w for w in got.warnings)
    assert got.context["X01"].source == "ticket" and got.context["X02"].source == "default"
    assert sent["output_config"]["format"]["schema"] == form_schema(MODEL)


def test_claude_reader_sends_only_redacted_text():
    client, sent = fake_client(blank_form())
    ClaudeReader(MODEL, CONFIG, client=client).read("Reported by jane.doe@example.ac.ug", "")
    assert "jane.doe@example.ac.ug" not in sent["messages"][0]["content"]


def test_claude_reader_raises_on_refusal():
    client, _ = fake_client(blank_form(), stop_reason="refusal")
    with pytest.raises(ReaderError):
        ClaudeReader(MODEL, CONFIG, client=client).read("ticket", "")


# ----- The trained agent ---------------------------------------------------------
AGENT_RUN = ROOT / "results" / "pilot" / "runs" / "phase5_shielded_seed0"   # the Phase 7 agent, for pilot_model.json


@pytest.mark.skipif(not (AGENT_RUN / "final.zip").exists(), reason="trained agent not saved locally")
@pytest.mark.parametrize("name", list(CASES))
def test_trained_agent_never_gets_a_prohibited_fix_through(name):
    from src.prototype.triage import load_agent
    model_agent = load_agent(AGENT_RUN)
    got = KeywordReader(MODEL, CONFIG).read(*case_text(name))
    report = triage(got, SCENARIO, MODEL, model_agent)
    decision = report["decision"]
    assert decision["outcome"] in ("fix", "escalated", "forced_escalation", "step_limit")
    if decision["outcome"] == "fix":
        observed = {s["action"].split()[1] for s in report["steps"] if s.get("result") in (POSITIVE, NEGATIVE)}
        for rule in MODEL["rules"]:
            if rule["cause"] == decision["cause"] and got.context[rule["when"]["attribute"]].value == rule["when"]["value"]:
                assert rule["unless_observed"] in observed
