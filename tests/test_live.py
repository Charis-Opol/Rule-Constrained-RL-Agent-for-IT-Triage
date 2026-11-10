"""Live incidents (src/prototype/live.py) and the local language model reader (local_llm.py)."""
import json
from pathlib import Path

import pytest

from src.prototype import live
from src.prototype.cli import load_inputs, make_reader
from src.prototype.delegate import make_delegate
from src.prototype.local_llm import LocalDelegate, LocalReader
from src.prototype.reading import NEGATIVE, POSITIVE, PRESENT
from src.prototype.triage import load_agent, run_settings

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def setup():
    _, config, _ = load_inputs()
    model, config, scenario = load_inputs(settings_path=str(run_settings(ROOT / config["agent_run"],
                                                                         ROOT / config["settings"])))
    return model, config, scenario, load_agent(ROOT / config["agent_run"])


def test_same_seed_same_incident_and_different_seeds_differ(setup):
    model, _, scenario, _ = setup
    a, b = live.draw(model, scenario, 5), live.draw(model, scenario, 5)
    assert (a.cause, a.ticket, a.logs, a.results) == (b.cause, b.ticket, b.logs, b.results)
    assert len({live.draw(model, scenario, s).logs for s in range(10)}) == 10


def test_the_ticket_and_log_never_name_the_cause(setup):
    model, _, scenario, _ = setup
    for seed in range(40):
        inc = live.draw(model, scenario, seed)
        text = (inc.ticket + inc.logs).lower()
        assert inc.cause.lower() not in text
        for c in model["causes"]:
            assert c["name"].lower() not in text and c["remedy"].lower() not in text


def test_keyword_reader_reads_the_written_evidence_as_drawn(setup):
    """The text says what the hidden system shows: the keyword reader, which the format is
    written for, makes no mistakes, so any wrong decision comes from reversed results."""
    model, config, scenario, _ = setup
    reader = make_reader("keyword", model, config)
    for seed in range(150):
        inc = live.draw(model, scenario, seed)
        assert live.reading_errors(reader.read(inc.ticket, inc.logs), inc, model) == [], seed


def test_chosen_cause_is_kept_and_checks_not_in_the_log_are_probed(setup):
    model, config, scenario, agent = setup
    inc = live.draw(model, scenario, 3, cause="C02")
    assert inc.cause == "C02" and inc.origin == "chosen"
    reading, report = live.run(inc, make_reader("keyword", model, config), scenario, model, agent, config,
                               delegate=make_delegate("pattern", config), staging=False)
    for step in report["steps"]:
        if step["action"].startswith("Run") and step.get("source") == "probe":
            cid = step["action"].split()[1]
            assert cid not in inc.in_logs and cid in inc.probes
            assert step["result"] == (POSITIVE if inc.results[cid] else NEGATIVE)
        assert len(step["belief"]) == len(model["causes"]) and step["alternatives"]


def test_a_fix_clears_the_symptoms_only_for_the_hidden_cause(setup):
    model, _, scenario, _ = setup
    inc = live.draw(model, scenario, 8, cause="C06")
    check = live.Remeasure(inc)
    assert check({"id": "C06"}, {}).cleared is True
    assert check({"id": "C02"}, {}).cleared is False


def test_code_fault_fixes_are_judged_by_the_hidden_faults_reproduction_tests(setup):
    model, config, scenario, _ = setup
    inc = live.draw(model, scenario, 2, cause="C08")
    verify = live.live_verifier(inc, config["actions"], staging=True)
    causes = {c["id"]: c for c in model["causes"]}
    right, wrong = verify(causes["C08"], {}), verify(causes["C05"], {})
    assert right.cleared is True and right.how == "staging tests"
    assert wrong.cleared is False and wrong.how == "staging tests"


def test_outcomes_over_many_incidents_never_include_a_wrong_fix(setup):
    model, config, scenario, agent = setup
    reader, delegate = make_reader("keyword", model, config), make_delegate("pattern", config)
    for seed in range(60):
        inc = live.draw(model, scenario, 1000 + seed)
        _, report = live.run(inc, reader, scenario, model, agent, config, delegate=delegate, staging=False)
        assert live.outcome(report, inc) != "wrong fix"
        if report["decision"]["outcome"] == "fix":
            assert report["decision"]["cause"] == inc.cause


def test_own_ticket_fixes_symptoms_context_and_stated_checks(setup):
    model, config, scenario, _ = setup
    ticket = "Students cannot log in to the portal. Only some students have it, others are fine. Priority: low."
    reading = make_reader("keyword", model, config).read(ticket, "")
    inc = live.from_ticket(reading, ticket, model, scenario, 4)
    assert inc.origin == "your ticket" and inc.ticket == ticket
    assert inc.symptoms == {k: f.value == PRESENT for k, f in reading.symptoms.items()}
    assert inc.context["X02"] == "Low" and inc.results["D10"] is True
    assert "D11" in inc.in_logs and "Traceback" in inc.logs


class FakeLLM:
    label = "fake"

    def __init__(self, answer):
        self.answer, self.calls = answer, []

    def chat(self, system, prompt, schema):
        self.calls.append(schema)
        return self.answer


def test_local_reader_fills_the_same_form_and_discards_invented_quotes(setup):
    model, config, _, _ = setup
    ticket, logs = "Users see a server error on the fees page.", "2026-11-10T08:00:00Z INFO cache hit_rate=0.97"
    answer = {"category": "unclear", "summary": "errors",
              "symptoms_shown": [{"symptom": "S01 Users see a server error on a page",
                                  "quote": "Users see a server error on the fees page."}],
              "context": {"X01 Affected system is production": {"value": "not_stated", "quote": ""}},
              "check_results": [{"check": "D08 Cache errors in logs", "result": "negative",
                                 "quote": "INFO cache hit_rate=0.97"},
                                {"check": "D02 Lock-wait errors in logs", "result": "positive",
                                 "quote": "deadlock detected"}]}             # not in the text
    reading = LocalReader(model, config, llm=FakeLLM(answer)).read(ticket, logs)
    assert reading.symptoms["S01"].value == PRESENT and reading.checks["D08"].value == NEGATIVE
    assert reading.checks["D02"].value == "not_shown" and reading.warnings
    assert reading.context["X01"].source == "default"


def test_hybrid_reader_takes_the_ticket_from_the_model_and_the_log_from_the_patterns(setup):
    model, config, scenario, _ = setup
    from src.prototype.local_llm import HybridReader
    inc = live.draw(model, scenario, 21)
    llm = FakeLLM({"category": "unclear", "summary": "", "symptoms_shown": [], "context": {},
                   "check_results": [{"check": "D03 DB connection pool usage", "result": "positive",
                                      "quote": "made up"}]})
    reading = HybridReader(model, config, llm=llm).read(inc.ticket, inc.logs)
    keyword = make_reader("keyword", model, config).read(inc.ticket, inc.logs)
    for cid, f in keyword.checks.items():
        if f.source == "logs":
            assert reading.checks[cid].value == f.value
    assert "+ log patterns" in reading.reader


def test_local_delegate_answers_in_the_delegate_form(setup):
    model, _, _, _ = setup
    d11 = next(c for c in model["checks"] if c.get("delegated"))
    logs = '2026-11-10T08:00:00Z ERROR api   File "portal/auth.py", line 40, in sign_in'
    answer = {"result": "positive", "evidence": 'File "portal/auth.py", line 40, in sign_in', "report": "auth.py"}
    result = LocalDelegate(llm=FakeLLM(answer)).analyse(d11, "ticket", logs)
    assert result.finding.value == POSITIVE and not result.warning
    assert json.dumps(result.to_dict())
