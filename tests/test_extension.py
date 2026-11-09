"""9 Nov 2026 extension: overlap (omega), pilot model v2 with the delegated check D11, the
delegate, and the action layer (routing, draft pull requests, simulated messages).

The evaluated core is unchanged: with omega = 0 the scenario is exactly the Phase 5 one, and
the action layer can only act on a decision that the rule checker confirmed."""
import json
import shutil
import subprocess
import types
from pathlib import Path

import numpy as np
import pytest

from experiments.pilot.build_model_v2 import extend

from src.prototype.actions import (ActionRefused, LocalRepo, Patch, PrewrittenPatcher, _run, act, check_patch,
                                   draft_pull_request, route)
from src.prototype.delegate import ClaudeDelegate, PatternDelegate, prompt_for
from src.prototype.reading import NEGATIVE, NOT_MENTIONED, NOT_SHOWN, POSITIVE, PRESENT, Finding, KeywordReader, Reading
from src.prototype.triage import triage
from src.sim.scenario import apply_overlap, build_scenario

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "experiments" / "pilot"
BASE = json.loads((PILOT / "pilot_model.json").read_text(encoding="utf-8"))
SETTINGS = json.loads((PILOT / "pilot_settings.json").read_text(encoding="utf-8"))
CONFIG = json.loads((PILOT / "prototype_config.json").read_text(encoding="utf-8"))
MODEL = extend(BASE, json.loads((PILOT / "pilot_additions_provisional.json").read_text(encoding="utf-8")))
SETTINGS_V2 = {**SETTINGS, "max_steps": 13}
SCENARIO = build_scenario(MODEL, SETTINGS_V2)
EXAMPLES = ROOT / "prototype" / "examples"

N_CHECKS, ESCALATE = 11, 19
D07, D08, D11 = 6, 7, 10
FIX = {c["id"]: N_CHECKS + j for j, c in enumerate(MODEL["causes"])}
HAS_GIT = shutil.which("git") is not None


class Scripted:
    def __init__(self, order):
        self.order = order

    def q_values(self, obs_with_mask):
        mask = np.asarray(obs_with_mask)[-(ESCALATE + 1):] > 0.5
        q = np.full(ESCALATE + 1, -5.0)
        for rank, action in enumerate(self.order):
            q[action] = 10.0 - rank
        q[~mask] = -np.inf
        return q


def case(name):
    folder = EXAMPLES / name
    return (folder / "ticket.txt").read_text(encoding="utf-8"), (folder / "logs.txt").read_text(encoding="utf-8")


def reading(production="No", checks=None):
    symptoms = {s["id"]: Finding(PRESENT if s["id"] == "S02" else NOT_MENTIONED) for s in MODEL["symptoms"]}
    found = {c["id"]: Finding((checks or {}).get(c["id"], NOT_SHOWN), "line", "logs") for c in MODEL["checks"]}
    context = {"X01": Finding(production, source="ticket"), "X02": Finding("Low", source="ticket")}
    return Reading("test", "Database", "", symptoms, context, found)


# ----- Overlap (omega) -------------------------------------------------------------
def test_zero_overlap_leaves_the_phase5_scenario_unchanged():
    assert np.array_equal(build_scenario(BASE, SETTINGS).theta, np.array(BASE["check_likelihoods"]))
    assert np.array_equal(build_scenario(BASE, {**SETTINGS, "overlap": 0.0}).theta, np.array(BASE["check_likelihoods"]))


def test_full_overlap_makes_causes_in_a_category_identical():
    categories = [c["category"] for c in BASE["causes"]]
    theta = build_scenario(BASE, {**SETTINGS, "overlap": 1.0}).theta
    database = [j for j, c in enumerate(categories) if c == "Database"]
    assert np.allclose(theta[:, database], theta[:, database[:1]])
    sole = categories.index("Authentication and access")          # one cause: nothing to average with
    assert np.allclose(theta[:, sole], np.array(BASE["check_likelihoods"])[:, sole])


def test_overlap_is_the_chapter3_formula():
    theta = np.array([[0.9, 0.1, 0.5]])
    got = apply_overlap(theta, ["A", "A", "B"], 0.25)
    assert np.allclose(got, [[0.75 * 0.9 + 0.25 * 0.5, 0.75 * 0.1 + 0.25 * 0.5, 0.5]])
    with pytest.raises(ValueError):
        apply_overlap(theta, ["A", "A", "B"], 1.5)


# ----- Model v2 ----------------------------------------------------------------------
def test_v2_adds_one_delegated_check_and_keeps_the_rest():
    assert len(MODEL["checks"]) == 11 and MODEL["checks"][-1]["delegated"] is True
    assert MODEL["check_likelihoods"][:10] == BASE["check_likelihoods"]
    assert all("owner" in c and isinstance(c["code_fault"], bool) for c in MODEL["causes"])
    assert BASE["checks"][-1]["id"] == "D10"                    # the Phase 5 model is untouched
    assert SCENARIO.theta.shape == (11, 8)


def test_readers_leave_the_delegated_check_to_the_agent():
    from src.prototype.llm import form_schema
    assert "D11" not in form_schema(MODEL)["properties"]["checks"]["properties"]
    got = KeywordReader(MODEL, CONFIG).read(*case("class_results_slow"))
    assert got.checks["D11"].value == NOT_SHOWN


# ----- Delegate ----------------------------------------------------------------------
def test_pattern_delegate_answers_in_the_checks_terms():
    d11 = MODEL["checks"][D11]
    assert PatternDelegate(CONFIG).analyse(d11, *case("class_results_slow")).finding.value == POSITIVE
    assert PatternDelegate(CONFIG).analyse(d11, *case("profile_cache")).finding.value == POSITIVE
    assert PatternDelegate(CONFIG).analyse(d11, *case("payment_gateway")).finding.value == NOT_SHOWN
    library_only = 'Traceback (most recent call last):\n  File "sqlalchemy/engine.py", line 9, in run'
    assert PatternDelegate(CONFIG).analyse(d11, "", library_only).finding.value == NEGATIVE


def test_the_prompt_is_a_fixed_template_from_the_check():
    d11 = MODEL["checks"][D11]
    prompt = prompt_for(d11, "ticket text", "log text")
    assert d11["tests"] in prompt and d11["positive_means"] in prompt and "<logs>\nlog text\n</logs>" in prompt


def fake_client(answer):
    sent = {}

    def create(**kwargs):
        sent.update(kwargs)
        return types.SimpleNamespace(stop_reason="end_turn",
                                     content=[types.SimpleNamespace(type="text", text=json.dumps(answer))])
    return types.SimpleNamespace(beta=types.SimpleNamespace(messages=types.SimpleNamespace(create=create))), sent


def test_claude_delegate_discards_an_invented_quote():
    client, _ = fake_client({"result": "positive", "evidence": 'File "portal/made_up.py", line 1', "report": "r"})
    got = ClaudeDelegate(client=client).analyse(MODEL["checks"][D11], *case("profile_cache"))
    assert got.finding.value == NOT_SHOWN and got.warning


def test_claude_delegate_keeps_a_verified_quote_and_redacts_first():
    quote = 'File "portal/cache.py", line 11, in put'
    client, sent = fake_client({"result": "positive", "evidence": quote, "report": "Traced to the cache."})
    ticket = "Reported by jane.doe@example.ac.ug"
    got = ClaudeDelegate(client=client).analyse(MODEL["checks"][D11], ticket, case("profile_cache")[1])
    assert got.finding.value == POSITIVE and got.report == "Traced to the cache."
    assert "jane.doe@example.ac.ug" not in sent["messages"][0]["content"]


def test_the_agent_chooses_to_delegate_and_receives_only_the_result():
    ticket, logs = case("class_results_slow")
    report = triage(reading(), SCENARIO, MODEL, Scripted([D11, FIX["C04"]]), delegate=PatternDelegate(CONFIG),
                    ticket=ticket, logs=logs)
    first = report["steps"][0]
    assert first["result"] == POSITIVE and first["delegation"]["report"]
    assert report["decision"]["cause"] == "C04" and report["decision"]["permitted"] is True


def test_without_a_delegate_the_delegated_check_is_unavailable():
    report = triage(reading(), SCENARIO, MODEL, Scripted([D11, ESCALATE]))
    assert report["steps"][0]["result"] == "unavailable"


# ----- Routing -----------------------------------------------------------------------
def fake_report(outcome="fix", cause="C04", permitted=True, top=("C02", 0.7)):
    decision = {"outcome": outcome, "checks_run": 1, "check_minutes": 30, "blocked_proposals": 0}
    if outcome == "fix":
        c = next(x for x in MODEL["causes"] if x["id"] == cause)
        decision.update(cause=cause, cause_name=c["name"], remedy=c["remedy"], permitted=permitted)
    else:
        decision["reason"] = "The agent judged the evidence too weak or too risky to act on."
    return {"reading": {"warnings": []}, "steps": [{"action": "Run D11 Full log analysis", "result": "positive",
                                                     "evidence": "x", "source": "delegate (logs)"}],
            "decision": decision, "reference": [{"cause": top[0], "name": "n", "probability": top[1]}]}


def test_routing_goes_to_the_owner_or_the_fallback():
    assert route(fake_report(), MODEL)[0] == "Application team lead"
    assert route(fake_report("escalated", top=("C02", 0.7)), MODEL)[0] == "Database administrator"
    assert route(fake_report("escalated", top=("C02", 0.3)), MODEL)[0] == "Senior developer"


# ----- Action layer guarantees ---------------------------------------------------------
def test_only_allowed_commands_run_and_nothing_merges(tmp_path):
    for cmd in (["git", "merge", "x"], ["gh", "pr", "merge", "1"], ["gh", "pr", "create", "--title", "t"],
                ["git", "push", "origin", "main"], ["git", "push", "--force", "origin", "b"], ["rm", "-rf", "."]):
        with pytest.raises(ActionRefused):
            _run(cmd, tmp_path)


def test_no_pull_request_without_a_confirmed_fix(tmp_path):
    repo = LocalRepo(tmp_path / "repo", ROOT / "prototype" / "toy_repo")
    patcher = PrewrittenPatcher(ROOT / "prototype" / "toy_repo_fixes")
    cause = next(c for c in MODEL["causes"] if c["id"] == "C04")
    for report in (fake_report(permitted=False), fake_report("escalated")):
        with pytest.raises(ActionRefused):
            draft_pull_request(report, MODEL, cause, repo, patcher, "t1", "owner")
    c02 = next(c for c in MODEL["causes"] if c["id"] == "C02")      # not a code fault
    with pytest.raises(ActionRefused):
        draft_pull_request(fake_report(cause="C02"), MODEL, c02, repo, patcher, "t1", "owner")
    assert not (tmp_path / "repo").exists()                        # refused before touching anything


def test_a_patch_may_only_change_an_existing_source_file():
    repo = ROOT / "prototype" / "toy_repo"
    for path in ("tests/test_portal.py", "portal/new.py", "../outside.py", ".github/workflows/x.yml"):
        with pytest.raises(ActionRefused):
            check_patch(Patch(path, "x = 1\n", "", "test"), repo)
    check_patch(Patch("portal/results.py", "x = 1\n", "", "test"), repo)


def test_act_refuses_an_unconfirmed_fix(tmp_path):
    settings = {"outbox": str(tmp_path / "outbox"), "local_repo": str(tmp_path / "repo"),
                "toy_repo": str(ROOT / "prototype" / "toy_repo"), "fixes": str(ROOT / "prototype" / "toy_repo_fixes")}
    with pytest.raises(ActionRefused):
        act(fake_report(permitted=False), MODEL, settings, "t1", "ticket")


def test_escalation_writes_a_routed_handover_and_opens_nothing(tmp_path):
    settings = {"outbox": str(tmp_path / "outbox"), "local_repo": str(tmp_path / "repo")}
    got = act(fake_report("escalated", top=("C02", 0.8)), MODEL, settings, "t1", "Approvals fail")
    assert got["kind"] == "escalation" and got["owner"] == "Database administrator"
    assert "Approvals fail" in Path(got["message"]).read_text(encoding="utf-8")
    assert not (tmp_path / "repo").exists()


@pytest.mark.skipif(not HAS_GIT, reason="git not installed")
def test_end_to_end_local_draft_pull_request(tmp_path):
    """class_results_slow: the agent delegates, fixes C04, and a branch with the fix is
    committed; the toy repository's tests pass on it, and main is left as it was."""
    ticket, logs = case("class_results_slow")
    report = triage(reading(), SCENARIO, MODEL, Scripted([D11, D07, FIX["C04"]]), delegate=PatternDelegate(CONFIG),
                    ticket=ticket, logs=logs)
    settings = {"outbox": str(tmp_path / "outbox"), "local_repo": str(tmp_path / "repo"),
                "toy_repo": str(ROOT / "prototype" / "toy_repo"), "fixes": str(ROOT / "prototype" / "toy_repo_fixes")}
    got = act(report, MODEL, settings, "class_results_slow", ticket)
    assert got["kind"] == "draft_pull_request", got
    pr = got["pull_request"]
    assert pr["patch"] == "portal/results.py" and pr["tests"].startswith("1 fixed, 0 broken")
    repo = tmp_path / "repo"
    branches = subprocess.run(["git", "branch"], cwd=repo, capture_output=True, text=True).stdout
    assert pr["branch"] in branches
    main_file = (repo / "portal" / "results.py").read_text(encoding="utf-8")
    assert main_file == (ROOT / "prototype" / "toy_repo" / "portal" / "results.py").read_text(encoding="utf-8")
    assert "draft" in Path(got["message"]).read_text(encoding="utf-8").lower()


def test_judge_tests_needs_a_fix_and_no_breakage():
    from src.prototype.actions import judge_tests
    before = {"a": False, "b": True}
    assert judge_tests(before, {"a": True, "b": True})[0] is True
    assert judge_tests(before, {"a": True, "b": False})[0] is False      # broke b
    assert judge_tests(before, {"a": False, "b": True})[0] is False      # fixed nothing


@pytest.mark.skipif(not HAS_GIT, reason="git not installed")
def test_a_patch_that_breaks_the_tests_opens_no_pull_request(tmp_path):
    class Breaker:
        name = "breaker"

        def write(self, cause, report, repo):
            return Patch("portal/db.py", "raise ImportError('broken')\n", "breaks everything", "test")

    repo = LocalRepo(tmp_path / "repo", ROOT / "prototype" / "toy_repo")
    cause = next(c for c in MODEL["causes"] if c["id"] == "C04")
    with pytest.raises(ActionRefused, match="tests"):
        draft_pull_request(fake_report(), MODEL, cause, repo, Breaker(), "t1", "owner")
