"""Builds pilot model v2: the pilot model plus the Part 2 additions.

    python -m experiments.pilot.build_model_v2                      # researcher-provisional additions
    python -m experiments.pilot.build_model_v2 --workbook "research/elicitation/private/Part 2 Responses.xlsx"

The additions are a delegated check (D11, a full log analysis by a language model), and for each
cause whether it is fixed by a code change and who is in charge of it. pilot_model.json is not
changed, so the Phase 5 results still reproduce from it. With --workbook, the developer's sample
tickets are also written to prototype/examples/developer/ for the reader test.
"""
import argparse
import json
import warnings
from pathlib import Path

from openpyxl import load_workbook

PILOT = Path(__file__).resolve().parent
ROOT = PILOT.parents[1]
BASE = PILOT / "pilot_model.json"
PROVISIONAL = PILOT / "pilot_additions_provisional.json"
OUT_MODEL, OUT_SETTINGS = PILOT / "pilot_model_v2.json", PILOT / "pilot_settings_v2.json"
DEVELOPER_CASES = ROOT / "prototype" / "examples" / "developer"
RESULTS = ("positive", "negative", "not shown")


def _text(value):
    return str(value).strip() if value is not None else ""


def read_part2(path, base):
    """The additions, in the same shape as pilot_additions_provisional.json, plus sample tickets."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        wb = load_workbook(path, data_only=True)
    cause_ids = [c["id"] for c in base["causes"]]

    ws = wb["Causes"]
    causes = {}
    for row in range(6, 6 + len(cause_ids)):
        cause_id = _text(ws[f"A{row}"].value)
        code, owner = _text(ws[f"E{row}"].value), _text(ws[f"F{row}"].value)
        if cause_id not in cause_ids:
            raise ValueError(f"Causes!A{row}: unexpected id {cause_id!r}")
        if code not in ("Yes", "No") or not owner:
            raise ValueError(f"Causes row {row} ({cause_id}): fill in both 'code change' and 'in charge'")
        causes[cause_id] = {"code_fault": code == "Yes", "owner": owner}
    fallback = _text(ws["F16"].value) or "Senior developer"

    ws = wb["New check"]
    check = {"id": "D11", "name": _text(ws["B6"].value), "tests": _text(ws["B7"].value),
             "positive_means": _text(ws["B8"].value), "effort": _text(ws["B9"].value), "delegated": True,
             "ratings": {}}
    for row in range(14, 14 + len(cause_ids)):
        cause_id, rating = _text(ws[f"A{row}"].value), _text(ws[f"C{row}"].value)
        if rating not in base["scale"]:
            raise ValueError(f"New check!C{row} ({cause_id}): choose a rating")
        check["ratings"][cause_id] = rating

    ws = wb["Sample tickets"]
    check_ids = [c["id"] for c in base["checks"]] + ["D11"]
    tickets = []
    for row in range(6, ws.max_row + 1):
        text = _text(ws[f"B{row}"].value)
        if not text:
            continue
        expected = {}
        for k, check_id in enumerate(check_ids):
            value = _text(ws.cell(row, 8 + k).value).lower()
            if value and value not in RESULTS:
                raise ValueError(f"Sample tickets row {row}, {check_id}: {value!r}")
            if value in ("positive", "negative"):
                expected[check_id] = value
        tickets.append({"id": _text(ws[f"A{row}"].value), "ticket": text, "logs": _text(ws[f"C{row}"].value),
                        "true_cause": _text(ws[f"D{row}"].value), "production": _text(ws[f"E{row}"].value),
                        "priority": _text(ws[f"F{row}"].value),
                        "symptoms_present": [s.strip() for s in _text(ws[f"G{row}"].value).split(",") if s.strip()],
                        "checks": expected})
    return {"source": "pilot developer (Part 2)", "checks": [check], "causes": causes,
            "fallback_owner": fallback}, tickets


def extend(base, additions):
    model = json.loads(json.dumps(base))
    model["label"] = "pilot v2"
    model["additions_source"] = additions["source"]
    model["fallback_owner"] = additions["fallback_owner"]
    cause_ids = [c["id"] for c in model["causes"]]
    for cause in model["causes"]:
        cause.update(additions["causes"][cause["id"]])
    for check in additions["checks"]:
        ratings = check["ratings"]
        model["checks"].append({k: check[k] for k in ("id", "name", "tests", "positive_means", "effort", "delegated")})
        model["check_likelihoods"].append([model["scale"][ratings[c]] for c in cause_ids])
    return model


def write_developer_cases(tickets, model):
    DEVELOPER_CASES.mkdir(parents=True, exist_ok=True)
    cases = {}
    for t in tickets:
        folder = DEVELOPER_CASES / t["id"]
        folder.mkdir(exist_ok=True)
        (folder / "ticket.txt").write_text(t["ticket"] + "\n", encoding="utf-8")
        if t["logs"]:
            (folder / "logs.txt").write_text(t["logs"] + "\n", encoding="utf-8")
        category = next((c["category"] for c in model["causes"] if c["id"] == t["true_cause"]), "unclear")
        context = {}
        if t["production"]:
            context["X01"] = t["production"]
        if t["priority"]:
            context["X02"] = t["priority"]
        cases[t["id"]] = {"intended_cause": t["true_cause"] or None,
                          "expected": {"category": category, "symptoms_present": t["symptoms_present"],
                                       "context": context, "checks": t["checks"]}}
    (DEVELOPER_CASES / "cases.json").write_text(json.dumps(
        {"note": "Written by the pilot developer (Part 2 workbook), not by the researcher. Pilot only.",
         "cases": cases}, indent=1) + "\n", encoding="utf-8")
    return len(cases)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--workbook", type=Path, help="the developer's filled-in Part 2 workbook")
    args = parser.parse_args()
    base = json.loads(BASE.read_text(encoding="utf-8"))
    tickets = []
    if args.workbook:
        additions, tickets = read_part2(args.workbook, base)
    else:
        additions = json.loads(PROVISIONAL.read_text(encoding="utf-8"))
    model = extend(base, additions)
    OUT_MODEL.write_text(json.dumps(model, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    settings = json.loads((PILOT / "pilot_settings.json").read_text(encoding="utf-8"))
    settings["label"] = "pilot v2"
    settings["max_steps"] = len(model["checks"]) + 2       # every check, one block, one decision
    settings.setdefault("overlap", 0.0)
    OUT_SETTINGS.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    print(f"{OUT_MODEL.name}: {len(model['checks'])} checks ({additions['source']}); max_steps {settings['max_steps']}")
    if tickets:
        print(f"{write_developer_cases(tickets, model)} sample tickets in {DEVELOPER_CASES}")


if __name__ == "__main__":
    main()
