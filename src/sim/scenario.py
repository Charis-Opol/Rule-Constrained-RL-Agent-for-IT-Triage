"""The scenario model and settings as arrays, ready for the environment."""
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class Rule:
    id: str
    cause: int                  # index of the cause whose remedy is forbidden
    attribute: int              # index of the context attribute in the condition
    value: int                  # index of the value that activates the rule
    unless_observed: int | None   # index of the check that lifts the rule, if any

    def active(self, context):
        return context[self.attribute] == self.value


@dataclass(frozen=True)
class Scenario:
    theta: np.ndarray           # theta[i, j] = P(check i is positive | cause j)
    symptom_theta: np.ndarray   # symptom_theta[i, j] = P(symptom i is present | cause j)
    prior: np.ndarray           # P(cause j)
    check_costs: np.ndarray
    context_values: tuple       # per attribute, its values in workbook order
    context_probs: tuple        # per attribute, P(value)
    rules: tuple
    r_correct: float
    cost_wrong: float
    cost_esc: float
    p_noise: float
    p_miss: float
    max_steps: int
    overlap: float = 0.0        # omega in Chapter 3; theta above already includes it
    # Fix with verification (Phase 9, part B). Off by default: a fix then ends the episode, as
    # in v1/v2. On: a fix is applied and verified; a wrong one costs apply + harm and the
    # episode goes on, with that fix ruled out.
    verify: bool = False
    fix_costs: np.ndarray | None = None       # cost of applying each cause's remedy
    wrong_fix_harm: np.ndarray | None = None  # extra cost when that remedy was the wrong one
    max_failed_fixes: int = 0                  # after this many failed fixes, a person takes over

    @property
    def n_checks(self):
        return self.theta.shape[0]

    @property
    def n_causes(self):
        return self.theta.shape[1]

    @property
    def n_symptoms(self):
        return self.symptom_theta.shape[0]


def apply_overlap(theta, categories, omega):
    """Chapter 3: theta'_ij = (1 - omega) theta_ij + omega * mean of theta_i. over the causes in
    the same category as cause j. A category with one cause is unchanged."""
    if not 0.0 <= omega <= 1.0:
        raise ValueError("overlap must be between 0 and 1")
    theta = np.asarray(theta, dtype=float)
    out = theta.copy()
    categories = np.asarray(categories)
    for category in np.unique(categories):
        cols = np.flatnonzero(categories == category)
        mean = theta[:, cols].mean(axis=1, keepdims=True)
        out[:, cols] = (1 - omega) * theta[:, cols] + omega * mean
    return out


def build_scenario(model, settings):
    """Combines the elicited model with the researcher's settings."""
    weights = settings["frequency_weights"]
    for cause in model["causes"]:
        if cause["frequency"] not in weights:
            raise ValueError(f"{cause['id']}: no weight for frequency {cause['frequency']!r}")
    prior = np.array([weights[c["frequency"]] for c in model["causes"]], dtype=float)
    prior /= prior.sum()

    minutes = settings["check_minutes"]
    for check in model["checks"]:
        if check["effort"] not in minutes:
            raise ValueError(f"{check['id']}: no minutes for effort {check['effort']!r}")
    unit = settings["reward_unit_minutes"]
    check_costs = np.array([minutes[c["effort"]] / unit for c in model["checks"]])

    cost_esc = model["costs"]["escalation_minutes"] / unit
    cost_wrong = model["costs"]["wrong_fix_multiple"] * cost_esc
    r_correct = settings["correct_reward"]
    if not r_correct > -cost_esc > -cost_wrong:
        raise ValueError("Rewards must satisfy correct > escalate > wrong")

    values, probs = [], []
    for attribute in model["context"]:
        p = settings["context_probabilities"][attribute["id"]]
        if set(p) != set(attribute["values"]):
            raise ValueError(f"{attribute['id']}: probabilities do not match its values")
        values.append(tuple(attribute["values"]))
        probs.append(np.array([p[v] for v in attribute["values"]], dtype=float))
        if not np.isclose(probs[-1].sum(), 1.0):
            raise ValueError(f"{attribute['id']}: probabilities do not sum to 1")

    cause_ids = [c["id"] for c in model["causes"]]
    check_ids = [c["id"] for c in model["checks"]]
    attribute_ids = [a["id"] for a in model["context"]]
    rules = []
    for rule in model["rules"]:
        attribute = attribute_ids.index(rule["when"]["attribute"])
        unless = rule["unless_observed"]
        rules.append(Rule(rule["id"], cause_ids.index(rule["cause"]), attribute,
                          values[attribute].index(rule["when"]["value"]),
                          check_ids.index(unless) if unless else None))

    verify, fix_costs, wrong_fix_harm, max_failed = _verification(settings, model, cause_ids, unit, cost_esc, r_correct)

    overlap = float(settings.get("overlap", 0.0))
    theta = apply_overlap(model["check_likelihoods"], [c["category"] for c in model["causes"]], overlap)
    return Scenario(theta=theta,
                    symptom_theta=np.array(model["symptom_likelihoods"]),
                    prior=prior, check_costs=check_costs,
                    context_values=tuple(values), context_probs=tuple(probs), rules=tuple(rules),
                    r_correct=r_correct, cost_wrong=cost_wrong, cost_esc=cost_esc,
                    p_noise=settings["p_noise"], p_miss=settings["p_miss"], max_steps=settings["max_steps"],
                    overlap=overlap, verify=verify, fix_costs=fix_costs, wrong_fix_harm=wrong_fix_harm,
                    max_failed_fixes=max_failed)


def _verification(settings, model, cause_ids, unit, cost_esc, r_correct):
    """Reads the fix_with_verification block. Mean harm of a wrong fix = (wrong_fix_multiple - 1)
    x escalation, so a wrong fix followed by escalation costs, on average, what one wrong fix cost
    in v1/v2; each remedy's harm_weight (normalised to mean 1) spreads it across remedies."""
    block = settings.get("fix_with_verification") or {}
    if not block.get("enabled"):
        return False, None, None, 0
    remedies = block["remedies"]
    missing = set(cause_ids) - set(remedies)
    if missing:
        raise ValueError(f"fix_with_verification: no remedy settings for {sorted(missing)}")
    weights = np.array([remedies[c]["harm_weight"] for c in cause_ids], dtype=float)
    if (weights <= 0).any():
        raise ValueError("fix_with_verification: harm weights must be positive")
    fix_costs = np.array([remedies[c]["apply_minutes"] / unit for c in cause_ids])
    mean_harm = (model["costs"]["wrong_fix_multiple"] - 1) * cost_esc
    harm = mean_harm * weights / weights.mean()
    if not (r_correct - fix_costs > -cost_esc).all():
        raise ValueError("fix_with_verification: a correct fix must beat escalation for every remedy")
    max_failed = int(block.get("max_failed_fixes", 2))
    if max_failed < 1:
        raise ValueError("fix_with_verification: max_failed_fixes must be at least 1")
    return True, fix_costs, harm, max_failed


def load_scenario(model_path, settings_path, escalation_minutes=None):
    """escalation_minutes overrides the elicited cost of escalation (sensitivity analysis only).
    The wrong-fix cost stays wrong_fix_multiple x escalation, so the elicited ratio is kept."""
    model = json.loads(Path(model_path).read_text(encoding="utf-8"))
    if escalation_minutes is not None:
        model["costs"] = {**model["costs"], "escalation_minutes": float(escalation_minutes)}
    return build_scenario(model, json.loads(Path(settings_path).read_text(encoding="utf-8")))
