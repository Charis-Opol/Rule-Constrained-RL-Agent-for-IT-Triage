"""Phase 2 gate: the safety mechanism enforces every pilot rule and follows review-then-escalate."""
import copy
import json
from pathlib import Path

import numpy as np
import pytest
from gymnasium.utils.env_checker import check_env

from src.rules.safety import RuleMonitor, SafetyMechanism
from src.sim.scenario import build_scenario
from src.sim.triage_env import TriageEnv

PILOT = Path(__file__).resolve().parents[1] / "experiments" / "pilot"
MODEL = json.loads((PILOT / "pilot_model.json").read_text(encoding="utf-8"))
SETTINGS = json.loads((PILOT / "pilot_settings.json").read_text(encoding="utf-8"))
SCENARIO = build_scenario(MODEL, SETTINGS)

N_CHECKS = 10
PROD, NOT_PROD = 0, 1                  # X01 values: Yes, No
LOW, MEDIUM, HIGH = 0, 1, 2            # X02 values
ESCALATE = 18

# Written out by hand from the workbook, so the tests do not trust the loader or the checker:
# rule id, cause index, check index, contexts where it applies, contexts where it does not.
RULES = [
    ("R01", 1, 4, (PROD, LOW), (NOT_PROD, HIGH)),
    ("R02", 5, 8, (PROD, MEDIUM), (NOT_PROD, HIGH)),
    ("R03", 6, 9, (PROD, HIGH), (NOT_PROD, LOW)),
    ("R04", 2, 5, (NOT_PROD, HIGH), (PROD, LOW)),
    ("R05", 0, 0, (PROD, LOW), (NOT_PROD, MEDIUM)),
]
UNRULED_CAUSES = [3, 4, 7]
FIX = {rule[0]: N_CHECKS + rule[1] for rule in RULES}


def incident(context=(PROD, HIGH), wrapper=SafetyMechanism, scenario=SCENARIO, **kwargs):
    """A fresh incident with the context set by hand and every check available."""
    env = wrapper(TriageEnv(scenario, p_noise=0.0))
    env.reset(seed=0, **kwargs)
    base = env.unwrapped
    base.context = np.array(context)
    base.available = np.ones(base.n_checks, dtype=bool)
    return env


def by_hand_forbidden(base, action):
    """An independent statement of the rules, for the randomised test."""
    production, priority = base.context
    observed = base.status >= base.NEGATIVE
    return ((action == 11 and production == PROD and not observed[4])
            or (action == 15 and production == PROD and not observed[8])
            or (action == 16 and production == PROD and not observed[9])
            or (action == 12 and priority == HIGH and not observed[5])
            or (action == 10 and production == PROD and not observed[0]))


# ----- Gate: each rule in each state -----------------------------------------
@pytest.mark.parametrize("rule_id,cause,check,applies,exempt", RULES)
def test_not_observed_blocks(rule_id, cause, check, applies, exempt):
    env = incident(applies)
    _, reward, done, _, info = env.step(N_CHECKS + cause)
    assert not done and reward == 0.0
    assert env.unwrapped.blocked_action == N_CHECKS + cause
    assert env.blocked == 1 and env.broken_rules == [rule_id]


@pytest.mark.parametrize("positive", [True, False])
@pytest.mark.parametrize("rule_id,cause,check,applies,exempt", RULES)
def test_observed_allows_whatever_the_result(rule_id, cause, check, applies, exempt, positive):
    env = incident(applies)
    env.unwrapped.reported[check] = positive
    env.step(check)
    *_, done, _, info = env.step(N_CHECKS + cause)
    assert done and info["outcome"] in ("correct", "wrong")
    assert info["blocked"] == 0


@pytest.mark.parametrize("rule_id,cause,check,applies,exempt", RULES)
def test_unavailable_does_not_count_as_observed(rule_id, cause, check, applies, exempt):
    env = incident(applies)
    env.unwrapped.available[check] = False
    env.step(check)
    assert not env.unwrapped.observed(check)
    *_, done, _, _ = env.step(N_CHECKS + cause)
    assert not done and env.blocked == 1


@pytest.mark.parametrize("rule_id,cause,check,applies,exempt", RULES)
def test_rule_is_ignored_in_the_wrong_context(rule_id, cause, check, applies, exempt):
    env = incident(exempt)
    *_, done, _, info = env.step(N_CHECKS + cause)
    assert done and info["outcome"] in ("correct", "wrong") and info["blocked"] == 0


@pytest.mark.parametrize("priority", [LOW, MEDIUM])
def test_r04_applies_only_at_high_priority(priority):
    *_, done, _, _ = incident((PROD, priority)).step(FIX["R04"])
    assert done


def test_another_check_does_not_lift_a_rule():
    env = incident((PROD, LOW))
    env.step(0)                        # D01 lifts R05, not R01
    assert not env.step(FIX["R01"])[2]


@pytest.mark.parametrize("cause", UNRULED_CAUSES)
def test_fixes_without_a_rule_always_pass(cause):
    for context in ((PROD, HIGH), (NOT_PROD, LOW)):
        assert incident(context).step(N_CHECKS + cause)[2]


def test_checks_and_escalation_are_never_blocked():
    for context in ((PROD, HIGH), (NOT_PROD, LOW)):
        for action in range(N_CHECKS):
            assert incident(context).step(action)[-1] == {}
        env = incident(context)
        env.step(FIX["R01"])           # even straight after a block
        assert env.action_masks()[ESCALATE]
        *_, done, _, info = env.step(ESCALATE)
        assert done and info["outcome"] == "escalated"


# ----- Gate: review-then-escalate --------------------------------------------
def test_block_tells_the_agent_and_masks_the_action():
    env = incident()
    before = env.unwrapped.t
    obs, reward, done, truncated, _ = env.step(FIX["R01"])
    assert (reward, done, truncated) == (0.0, False, False)
    assert env.unwrapped.t == before + 1
    assert obs[-1] == 1 and not env.action_masks()[FIX["R01"]]


def test_second_block_in_a_row_forces_an_escalation():
    env = incident()
    env.step(FIX["R01"])
    _, reward, done, _, info = env.step(FIX["R02"])
    assert done and reward == -2.0 and info["outcome"] == "forced_escalation"
    assert info["blocked"] == 2 and info["proposals"] == 2
    assert info["broken_rules"] == ["R01", "R02"] and info["executed_violations"] == 0


def test_repeating_the_blocked_action_also_forces_an_escalation():
    env = incident()
    env.step(FIX["R01"])
    assert env.step(FIX["R01"])[-1]["outcome"] == "forced_escalation"


def test_permitted_second_proposal_continues_normally():
    env = incident()
    env.step(FIX["R01"])
    obs, reward, done, *_ = env.step(0)
    assert not done and reward == pytest.approx(-5 / 60)
    assert obs[-1] == 0 and env.action_masks()[FIX["R01"]]    # flag and mask last one step


def test_agent_can_run_the_named_check_and_then_propose_again():
    env = incident()
    env.step(FIX["R01"])
    env.step(4)                        # D05 lifts R01
    *_, done, _, info = env.step(FIX["R01"])
    assert done and info["outcome"] in ("correct", "wrong")
    assert info["blocked"] == 1 and info["proposals"] == 3


def test_blocks_separated_by_a_permitted_action_are_not_in_a_row():
    env = incident()
    env.step(FIX["R01"])
    env.step(0)
    assert not env.step(FIX["R02"])[2]
    assert env.blocked == 2


def test_block_on_the_last_step_ends_at_the_step_limit():
    env = incident()
    for k in range(env.unwrapped.max_steps - 1):
        env.step(0)
    *_, reward, done, _, info = env.step(FIX["R01"])
    assert done and reward == -2.0 and info["outcome"] == "step_limit" and info["blocked"] == 1


def test_mechanism_adds_only_its_block_step_to_the_episode():
    plain = incident()
    plain.step(ESCALATE)
    blocked = incident()
    blocked.step(FIX["R01"])
    blocked.step(ESCALATE)
    assert blocked.unwrapped.t == plain.unwrapped.t + 1


# ----- Gate: nothing prohibited ever executes --------------------------------
def random_episodes(env, n=4000, respect_masks=True):
    env.action_space.seed(0)
    infos, proposed_forbidden = [], 0
    for k in range(n):
        env.reset(seed=k)
        done = False
        while not done:
            mask = env.action_masks().astype(np.int8) if respect_masks else None
            action = env.action_space.sample(mask=mask)
            forbidden = by_hand_forbidden(env.unwrapped, action)
            proposed_forbidden += forbidden
            _, _, done, _, info = env.step(action)
            if forbidden and isinstance(env, SafetyMechanism):
                assert info.get("outcome") not in ("correct", "wrong")
        infos.append(info)
    return infos, proposed_forbidden


@pytest.mark.parametrize("respect_masks", [True, False])
@pytest.mark.parametrize("p_miss", [0.0, 0.4])
def test_no_prohibited_action_executes_under_random_play(p_miss, respect_masks):
    env = SafetyMechanism(TriageEnv(SCENARIO, p_miss=p_miss))
    infos, proposed = random_episodes(env, respect_masks=respect_masks)
    assert proposed > 0                # the test only means something if rules were tested
    assert sum(i["blocked"] for i in infos) == proposed
    assert sum(i["executed_violations"] for i in infos) == 0


def test_same_random_play_without_the_mechanism_does_violate():
    env = RuleMonitor(TriageEnv(SCENARIO))
    infos, proposed = random_episodes(env)
    assert proposed > 0
    assert sum(i["executed_violations"] for i in infos) == proposed


# ----- Monitor and penalty ---------------------------------------------------
def test_monitor_executes_and_records_without_blocking():
    env = incident(wrapper=RuleMonitor)
    obs, reward, done, _, info = env.step(FIX["R01"])
    assert done and reward in (5.0, -10.0) and obs[-1] == 0
    assert info["executed_violations"] == 1 and info["blocked"] == 0 and info["broken_rules"] == ["R01"]


def test_penalty_applies_only_to_a_violation():
    make = lambda: RuleMonitor(TriageEnv(SCENARIO, p_noise=0.0), penalty=10.0)
    env = make()
    env.reset(seed=0)
    base = env.unwrapped
    base.context = np.array((PROD, HIGH))
    fix = FIX["R01"]
    expected = 5.0 if base.cause == 1 else -10.0
    assert env.step(fix)[1] == expected - 10.0

    env = make()
    env.reset(seed=0)
    env.unwrapped.context = np.array((NOT_PROD, LOW))
    assert env.step(fix)[1] == expected


# ----- Rules come from the configuration -------------------------------------
def test_rule_without_a_named_check_cannot_be_lifted():
    model = copy.deepcopy(MODEL)
    model["rules"][0]["unless_observed"] = None
    env = incident(scenario=build_scenario(model, SETTINGS))
    for check in range(N_CHECKS):
        env.step(check)
    assert not env.step(FIX["R01"])[2]
    assert env.broken_rules == ["R01"]


def test_rule_without_a_named_check_gives_the_rule_label():
    model = copy.deepcopy(MODEL)
    model["rules"][0]["unless_observed"] = None
    env = TriageEnv(build_scenario(model, SETTINGS))
    reasons = set()
    for k in range(3000):
        env.reset(seed=k)
        if env.cause == 1 and env.context[0] == PROD:
            reasons.add(env.escalate_reason)
    assert reasons == {"rule"}


def test_removing_a_rule_from_the_configuration_removes_it():
    model = copy.deepcopy(MODEL)
    del model["rules"][0]
    env = incident(scenario=build_scenario(model, SETTINGS))
    assert env.step(FIX["R01"])[2]


def test_hand_written_rules_match_the_configuration():
    found = [(r.id, r.cause, r.unless_observed) for r in SCENARIO.rules]
    assert found == [(r[0], r[1], r[2]) for r in RULES]


# ----- Interfaces ------------------------------------------------------------
@pytest.mark.parametrize("wrapper", [SafetyMechanism, RuleMonitor])
def test_gymnasium_api(wrapper):
    check_env(wrapper(TriageEnv(SCENARIO)), skip_render_check=True)


def test_mechanism_does_not_change_the_incident():
    plain, wrapped = TriageEnv(SCENARIO), SafetyMechanism(TriageEnv(SCENARIO))
    for k in range(50):
        assert np.array_equal(plain.reset(seed=k)[0], wrapped.reset(seed=k)[0])
        assert plain.cause == wrapped.unwrapped.cause
