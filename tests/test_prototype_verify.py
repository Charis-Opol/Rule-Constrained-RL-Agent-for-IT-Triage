"""Fix, then verify, in the prototype (src/prototype/verify.py and LiveTriageEnv with v3 settings).

A scripted stand-in agent tries fixes in a fixed order, so the tests check the prototype's
handling of verification, not what a trained agent would choose."""
import json
import shutil
from pathlib import Path

import numpy as np
import pytest

from src.prototype.actions import PrewrittenPatcher, act, evidence_lines, handover
from src.prototype.reading import KeywordReader
from src.prototype.triage import LiveTriageEnv, triage
from src.prototype.verify import (AnswerVerifier, CaseVerifier, ChainVerifier, StagingVerifier, Verification,
                                  reproduction_tests)
from src.sim.scenario import load_scenario

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "experiments" / "pilot"
MODEL = json.loads((PILOT / "pilot_model_v2.json").read_text(encoding="utf-8"))
CONFIG = json.loads((PILOT / "prototype_config.json").read_text(encoding="utf-8"))
V3 = load_scenario(PILOT / "pilot_model_v2.json", PILOT / "pilot_settings_v3.json")
V2 = load_scenario(PILOT / "pilot_model_v2.json", PILOT / "pilot_settings_v2.json")
CASE = ROOT / "prototype" / "examples" / "class_results_slow"          # written to show C04
N_CHECKS = len(MODEL["checks"])
CAUSE = {c["id"]: c for c in MODEL["causes"]}
FIX = {c["id"]: N_CHECKS + j for j, c in enumerate(MODEL["causes"])}
ESCALATE = N_CHECKS + len(MODEL["causes"])
HAS_GIT = shutil.which("git") is not None


class Scripted:
    """Takes the first action in `order` that the mask allows; escalates otherwise."""

    def __init__(self, *order):
        self.order = list(order) + [ESCALATE]

    def q_values(self, full):
        mask = full[-(ESCALATE + 1):] > 0.5
        q = np.full(ESCALATE + 1, -np.inf)
        for rank, action in enumerate(self.order):
            if mask[action] and not np.isfinite(q).any():
                q[action] = 10.0 - rank
        return q


def reading():
    ticket = (CASE / "ticket.txt").read_text(encoding="utf-8")
    logs = (CASE / "logs.txt").read_text(encoding="utf-8")
    return KeywordReader(MODEL, CONFIG).read(ticket, logs), ticket, logs


def run(agent, verify, scenario=V3):
    r, ticket, logs = reading()
    return triage(r, scenario, MODEL, agent, ticket=ticket, logs=logs, verify=verify)


def test_v3_settings_need_a_verifier_and_v2_is_unchanged():
    with pytest.raises(ValueError, match="verifier"):
        LiveTriageEnv(V3, lambda i: None)
    report = run(Scripted(FIX["C05"]), verify=None, scenario=V2)
    assert report["decision"]["outcome"] == "fix" and report["decision"]["cause"] == "C05"
    assert "attempts" not in report["decision"] and "verified" not in report["decision"]


def test_a_failed_fix_is_flagged_masked_and_the_agent_goes_on():
    report = run(Scripted(FIX["C05"], FIX["C05"], FIX["C04"]), CaseVerifier("C04"))
    d = report["decision"]
    assert d["outcome"] == "fix" and d["cause"] == "C04" and d["verified"] is True
    assert [(a["cause"], a["cleared"]) for a in d["attempts"]] == [("C05", False), ("C04", True)]
    # C05 is not proposed twice: after it failed, its fix is masked
    assert [s["action"].split(":")[0] for s in report["steps"]] == ["Fix C05", "Fix C04"]
    assert report["steps"][0]["verification"]["cleared"] is False
    assert "FIX FAILED" in evidence_lines(report)[0]


def test_two_failed_fixes_hand_the_incident_to_a_person():
    report = run(Scripted(FIX["C05"], FIX["C08"], FIX["C04"]), CaseVerifier("C04"))
    d = report["decision"]
    assert d["outcome"] == "fix_limit" and "2 fixes" in d["reason"]
    text = handover(report, "Senior developer", "test", "x", "ticket")
    assert "did not clear the symptoms" in text and "C05" in text and "C08" in text


def test_without_an_answer_the_fix_awaits_verification():
    report = run(Scripted(FIX["C05"]), ChainVerifier(AnswerVerifier({})))
    d = report["decision"]
    assert d["outcome"] == "awaiting_verification" and d["cause"] == "C05" and d["verified"] is False
    assert d["attempts"][0]["how"] == "none"


def test_operator_answers_are_used_cause_by_cause():
    report = run(Scripted(FIX["C08"], FIX["C05"]), ChainVerifier(AnswerVerifier({"C08": False, "C05": True})))
    assert [(a["cause"], a["cleared"], a["how"]) for a in report["decision"]["attempts"]] == \
        [("C08", False, "operator"), ("C05", True, "operator")]


def test_staging_clears_only_the_fix_for_the_incidents_own_bug():
    staging = StagingVerifier(ROOT / "prototype" / "toy_repo", PrewrittenPatcher(ROOT / "prototype" / "toy_repo_fixes"),
                              reproduction_tests(CASE))
    wrong = staging(CAUSE["C05"], {"steps": []})        # fixes the cache bug, not the N+1 one
    right = staging(CAUSE["C04"], {"steps": []})
    assert wrong.cleared is False and "still fail" in wrong.detail and wrong.patch["path"] == "portal/cache.py"
    assert right.cleared is True and "now pass" in right.detail and right.patch["path"] == "portal/results.py"
    assert staging(CAUSE["C02"], {"steps": []}) is None  # not a code fault: the next verifier answers


def test_chain_takes_the_first_definite_answer():
    first = ChainVerifier(lambda c, r: None, lambda c, r: Verification(None, "none", ""),
                          AnswerVerifier({"C02": True}))
    assert first(CAUSE["C02"], {}).how == "operator"
    assert ChainVerifier()(CAUSE["C02"], {}).cleared is None


@pytest.mark.skipif(not HAS_GIT, reason="git not installed")
def test_a_verified_code_fix_opens_a_draft_pr_with_the_verified_patch(tmp_path):
    staging = StagingVerifier(ROOT / "prototype" / "toy_repo", PrewrittenPatcher(ROOT / "prototype" / "toy_repo_fixes"),
                              reproduction_tests(CASE))
    report = run(Scripted(FIX["C05"], FIX["C04"]), staging)
    assert report["decision"]["verified"] is True
    settings = {"outbox": str(tmp_path / "outbox"), "local_repo": str(tmp_path / "repo"),
                "toy_repo": str(ROOT / "prototype" / "toy_repo"), "fixes": "does-not-exist"}
    result = act(report, MODEL, settings, "verify-test", "ticket")
    assert result["kind"] == "draft_pull_request"
    assert result["pull_request"]["patch"] == "portal/results.py"
    assert "**Verified:** staging tests" in result["pull_request"]["body"]
    message = Path(result["message"]).read_text(encoding="utf-8")
    assert "verified" in message and "C05" in message           # the failed attempt is reported too
