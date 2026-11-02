"""The scenario model and settings as arrays, ready for the environment."""
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class Rule:
    cause: int                  # index of the cause whose remedy is forbidden
    attribute: int              # index of the context attribute in the condition
    value: int                  # index of the value that activates the rule
    unless_observed: int | None   # index of the check that lifts the rule, if any


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

    @property
    def n_checks(self):
        return self.theta.shape[0]

    @property
    def n_causes(self):
        return self.theta.shape[1]

    @property
    def n_symptoms(self):
        return self.symptom_theta.shape[0]


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
        rules.append(Rule(cause_ids.index(rule["cause"]), attribute,
                          values[attribute].index(rule["when"]["value"]),
                          check_ids.index(unless) if unless else None))

    return Scenario(theta=np.array(model["check_likelihoods"]),
                    symptom_theta=np.array(model["symptom_likelihoods"]),
                    prior=prior, check_costs=check_costs,
                    context_values=tuple(values), context_probs=tuple(probs), rules=tuple(rules),
                    r_correct=r_correct, cost_wrong=cost_wrong, cost_esc=cost_esc,
                    p_noise=settings["p_noise"], p_miss=settings["p_miss"], max_steps=settings["max_steps"])


def load_scenario(model_path, settings_path):
    return build_scenario(json.loads(Path(model_path).read_text(encoding="utf-8")),
                          json.loads(Path(settings_path).read_text(encoding="utf-8")))
