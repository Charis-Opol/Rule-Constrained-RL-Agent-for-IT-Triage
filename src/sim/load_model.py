"""Read an elicitation workbook into the scenario model JSON that the simulator uses.

Works on the pilot and the full Directorate workbook, which share sheet names and cell
positions: headers on row 4, an example on row 5, entries from row 6. Who filled in the
workbook is never read from it; provenance is passed in, so no name reaches the JSON.

    python -m src.sim.load_model WORKBOOK.xlsx OUTPUT.json --label pilot --rater "..."
"""
import argparse
import json
import re
import warnings
from pathlib import Path

from openpyxl import load_workbook

FIRST_ROW = 6
GRID_FIRST_COL = 4


def _text(cell):
    return str(cell.value).strip() if cell.value is not None else ""


def _entries(ws, name_col):
    """(row, id) for each row from FIRST_ROW whose name column has been filled in."""
    return [(row, _text(ws[f"A{row}"])) for row in range(FIRST_ROW, ws.max_row + 1)
            if _text(ws[f"{name_col}{row}"])]


def _scale(wb):
    ws = wb["Scale"]
    scale = {_text(ws[f"A{row}"]): ws[f"B{row}"].value for row in range(5, 11)}
    default = ws["B12"].value
    if default is None or None in scale.values():
        raise ValueError("Scale has no calculated values; open and save the workbook in Excel first")
    return scale, default


def _likelihoods(ws, cause_rows, column_rows, scale, default):
    """[column][cause] probabilities. Rows and columns keep the positions of their source tabs."""
    matrix = []
    for source_row in column_rows:
        col = GRID_FIRST_COL + source_row - FIRST_ROW
        probabilities = []
        for cause_row in cause_rows:
            rating = _text(ws.cell(cause_row, col))
            if rating and rating not in scale:
                raise ValueError(f"{ws.title}!{ws.cell(cause_row, col).coordinate}: unknown rating {rating!r}")
            probabilities.append(scale[rating] if rating else default)
        matrix.append(probabilities)
    return matrix


def _condition(text, context, where):
    """Turns 'Priority is High' or 'Affected system is production' into attribute and value."""
    if not text:
        return None
    for attribute in context:
        if text == attribute["name"]:
            return {"attribute": attribute["id"], "value": "Yes"}
        prefix = attribute["name"] + " is "
        if text.startswith(prefix):
            value = text[len(prefix):]
            if attribute["values"] and value not in attribute["values"]:
                raise ValueError(f"{where}: {value!r} is not a value of {attribute['name']!r}")
            return {"attribute": attribute["id"], "value": value}
    raise ValueError(f"{where}: cannot match condition {text!r} to a context attribute")


def _rules(ws, causes, checks, context):
    cause_by_remedy = {}
    for cause in causes:
        if cause["remedy"] in cause_by_remedy:
            raise ValueError(f"Remedy {cause['remedy']!r} is shared by more than one cause")
        cause_by_remedy[cause["remedy"]] = cause["id"]
    check_ids = {check["id"] for check in checks}

    rules = []
    for row, rule_id in _entries(ws, "B"):
        remedy = _text(ws[f"B{row}"])
        if remedy not in cause_by_remedy:
            raise ValueError(f"Rules!B{row}: {remedy!r} is not the remedy of any cause")
        unless = _text(ws[f"D{row}"]).split(" ", 1)[0] or None
        if unless and unless not in check_ids:
            raise ValueError(f"Rules!D{row}: {unless!r} is not a check")
        rules.append({"id": rule_id,
                      "cause": cause_by_remedy[remedy],
                      "when": _condition(_text(ws[f"C{row}"]), context, f"Rules!C{row}"),
                      "unless_observed": unless,
                      "reason": _text(ws[f"F{row}"])})
    return rules


def _costs(ws):
    multiple = re.search(r"\d+(\.\d+)?", _text(ws["B8"]))
    return {"escalation_minutes": ws["B6"].value,
            "wrong_fix_multiple": float(multiple.group()) if multiple else None}


def read_model(wb, label, rater):
    """Builds the model from a workbook opened with data_only=True."""
    scale, default = _scale(wb)

    ws = wb["Causes"]
    cause_entries = _entries(ws, "C")
    causes = [{"id": cause_id, "category": _text(ws[f"B{row}"]), "name": _text(ws[f"C{row}"]),
               "description": _text(ws[f"D{row}"]), "remedy": _text(ws[f"E{row}"]),
               "frequency": _text(ws[f"F{row}"])} for row, cause_id in cause_entries]

    ws = wb["Checks"]
    check_entries = _entries(ws, "B")
    checks = [{"id": check_id, "name": _text(ws[f"B{row}"]), "tests": _text(ws[f"C{row}"]),
               "positive_means": _text(ws[f"D{row}"]), "effort": _text(ws[f"E{row}"])}
              for row, check_id in check_entries]

    ws = wb["Symptoms"]
    symptom_entries = _entries(ws, "B")
    symptoms = [{"id": symptom_id, "name": _text(ws[f"B{row}"]), "reported_as": _text(ws[f"C{row}"])}
                for row, symptom_id in symptom_entries]

    ws = wb["Context"]
    context = [{"id": attribute_id, "name": _text(ws[f"B{row}"]),
                "values": [v.strip() for v in _text(ws[f"C{row}"]).split(",") if v.strip()]}
               for row, attribute_id in _entries(ws, "B")]

    cause_rows = [row for row, _ in cause_entries]
    return {
        "label": label,
        "rater": rater,
        "scale": scale,
        "default_probability": default,
        "causes": causes,
        "checks": checks,
        "symptoms": symptoms,
        "context": context,
        "rules": _rules(wb["Rules"], causes, checks, context),
        "costs": _costs(wb["Costs (optional)"]),
        # theta[i][j] = P(check i is positive | cause j), as in the thesis
        "check_likelihoods": _likelihoods(wb["Check likelihoods"], cause_rows,
                                          [row for row, _ in check_entries], scale, default),
        # symptom_theta[i][j] = P(symptom i is present | cause j)
        "symptom_likelihoods": _likelihoods(wb["Symptom likelihoods"], cause_rows,
                                            [row for row, _ in symptom_entries], scale, default),
    }


def open_workbook(path):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")               # openpyxl: extended data validation
        return load_workbook(path, data_only=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("workbook", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--label", required=True, help="e.g. pilot")
    parser.add_argument("--rater", required=True, help="role and experience, never a name")
    args = parser.parse_args()
    model = read_model(open_workbook(args.workbook), args.label, args.rater)
    args.output.write_text(json.dumps(model, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{args.output}: {len(model['causes'])} causes, {len(model['checks'])} checks, "
          f"{len(model['symptoms'])} symptoms, {len(model['rules'])} rules")


if __name__ == "__main__":
    main()
