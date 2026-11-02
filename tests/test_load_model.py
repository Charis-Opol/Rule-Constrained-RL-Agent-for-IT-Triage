"""Phase 0 gate: the scenario model JSON matches the workbook and carries no personal details.

Tests that need the responses workbook are skipped on a clone, because it is kept private.
"""
import json
from pathlib import Path

import pytest

from src.sim.load_model import open_workbook, read_model

ROOT = Path(__file__).resolve().parents[1]
ELICITATION = ROOT / "research" / "elicitation"
RESPONSES = ELICITATION / "private" / "Pilot Elicitation Workbook Responses.xlsx"
MODEL = ROOT / "experiments" / "pilot" / "pilot_model.json"
LABEL, RATER = "pilot", "Software developer, 3 years' experience (one rater, not Directorate data)"

needs_responses = pytest.mark.skipif(not RESPONSES.exists(), reason="private responses workbook not present")


@pytest.fixture(scope="module")
def model():
    return json.loads(MODEL.read_text(encoding="utf-8"))


@pytest.fixture
def template():
    return open_workbook(ELICITATION / "Pilot_Elicitation_Workbook.xlsx")


def fill_one_cause(wb):
    wb["Causes"]["C6"], wb["Causes"]["E6"] = "Cause A", "Fix A"
    wb["Checks"]["B6"] = "Check A"
    wb["Symptoms"]["B6"] = "Symptom A"


def test_sizes(model):
    assert [len(model[k]) for k in ("causes", "checks", "symptoms", "rules", "context")] == [8, 10, 4, 5, 2]
    assert len(model["check_likelihoods"]) == 10 and len(model["symptom_likelihoods"]) == 4
    assert all(len(row) == 8 for row in model["check_likelihoods"] + model["symptom_likelihoods"])


def test_probabilities_come_from_the_scale(model):
    allowed = set(model["scale"].values())
    assert allowed == {0.05, 0.25, 0.5, 0.75, 0.95}
    assert all(p in allowed for row in model["check_likelihoods"] + model["symptom_likelihoods"] for p in row)


def test_rules_resolve(model):
    found = [(r["id"], r["cause"], r["when"]["attribute"], r["when"]["value"], r["unless_observed"])
             for r in model["rules"]]
    assert found == [("R01", "C02", "X01", "Yes", "D05"), ("R02", "C06", "X01", "Yes", "D09"),
                     ("R03", "C07", "X01", "Yes", "D10"), ("R04", "C03", "X02", "High", "D06"),
                     ("R05", "C01", "X01", "Yes", "D01")]


def test_costs(model):
    assert model["costs"] == {"escalation_minutes": 120, "wrong_fix_multiple": 5.0}


@needs_responses
def test_json_is_what_the_loader_produces(model):
    assert read_model(open_workbook(RESPONSES), LABEL, RATER) == model


@needs_responses
def test_matches_the_probability_tabs(model):
    wb = open_workbook(RESPONSES)
    for key, tab in (("check_likelihoods", "Check probabilities"), ("symptom_likelihoods", "Symptom probabilities")):
        for i, row in enumerate(model[key]):
            for j, p in enumerate(row):
                assert wb[tab].cell(6 + j, 4 + i).value == pytest.approx(p)


@needs_responses
def test_no_personal_details(model):
    name_and_role = str(open_workbook(RESPONSES)["README"]["B13"].value)
    text = MODEL.read_text(encoding="utf-8").lower()
    for part in name_and_role.split(",")[0].split():
        assert part.lower() not in text


def test_blank_rating_takes_the_default(template):
    fill_one_cause(template)
    assert read_model(template, "t", "t")["check_likelihoods"] == [[0.05]]


def test_unknown_rating_is_refused(template):
    fill_one_cause(template)
    template["Check likelihoods"]["D6"] = "Maybe"
    with pytest.raises(ValueError, match="unknown rating"):
        read_model(template, "t", "t")


def test_rule_on_an_unknown_remedy_is_refused(template):
    fill_one_cause(template)
    template["Rules"]["B6"] = "Fix B"
    with pytest.raises(ValueError, match="not the remedy"):
        read_model(template, "t", "t")


def test_rule_condition_must_match_the_context(template):
    fill_one_cause(template)
    template["Rules"]["B6"], template["Rules"]["C6"] = "Fix A", "Weekend"
    with pytest.raises(ValueError, match="cannot match"):
        read_model(template, "t", "t")


def test_reads_the_full_directorate_workbook_layout():
    wb = open_workbook(ELICITATION / "Directorate_Elicitation_Workbook.xlsx")
    fill_one_cause(wb)
    wb["Check likelihoods"]["D6"] = "Often"
    wb["Symptom likelihoods"]["D6"] = "Rarely"
    model = read_model(wb, "t", "t")
    assert (model["check_likelihoods"], model["symptom_likelihoods"]) == ([[0.75]], [[0.25]])
