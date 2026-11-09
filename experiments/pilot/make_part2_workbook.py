"""Writes research/elicitation/Pilot_Elicitation_Workbook_Part2.xlsx: the follow-up questions
for the pilot developer (9 Nov 2026), pre-filled with their 8 causes and 10 checks.

    python -m experiments.pilot.make_part2_workbook

A separate file because saving the original workbook with openpyxl would delete its rating
drop-downs (an Excel extension openpyxl does not keep). Cell positions match read_part2 in
build_model_v2.py. The researcher's provisional answers are not shown, so they do not anchor
the developer's.
"""
import json
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

PILOT = Path(__file__).resolve().parent
ROOT = PILOT.parents[1]
OUT = ROOT / "research" / "elicitation" / "Pilot_Elicitation_Workbook_Part2.xlsx"
N_TICKETS = 20

YELLOW = PatternFill("solid", fgColor="FFF2CC")
GREY = PatternFill("solid", fgColor="E7E6E6")
BLUE = PatternFill("solid", fgColor="DDEBF7")
BOLD, TITLE = Font(bold=True), Font(bold=True, size=14)
WRAP = Alignment(wrap_text=True, vertical="top")


def header(ws, title, note, columns, widths):
    ws["A1"], ws["A2"] = title, note
    ws["A1"].font = TITLE
    ws["A2"].alignment = Alignment(wrap_text=False)
    for i, (name, width) in enumerate(zip(columns, widths), 1):
        cell = ws.cell(4, i, name)
        cell.font, cell.fill, cell.alignment = BOLD, BLUE, WRAP
        ws.column_dimensions[cell.column_letter].width = width


def dropdown(ws, values, cells):
    dv = DataValidation(type="list", formula1='"' + ",".join(values) + '"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(cells)


def main():
    model = json.loads((PILOT / "pilot_model.json").read_text(encoding="utf-8"))
    provisional = json.loads((PILOT / "pilot_additions_provisional.json").read_text(encoding="utf-8"))
    d11 = provisional["checks"][0]
    causes, checks = model["causes"], model["checks"]
    ratings = [k for k in model["scale"] if k != "Unrelated"]

    wb = Workbook()
    ws = wb.active
    ws.title = "README"
    rows = [
        ("Incident Triage: Pilot Workbook, Part 2", ""),
        ("Follow-up for the developer who filled in the pilot workbook. Thank you again.", ""),
        ("", ""),
        ("Why", "The prototype now does more than recommend. It can hand a heavy analysis to a language model "
                "(a full log analysis), open a DRAFT pull request for faults fixed by a code change, and send an "
                "escalation to the person in charge. These questions set that up for your 8 causes."),
        ("What I need", "1 Causes: for each cause, is it fixed by a code change, and who is in charge of it (a role, "
                        "not a name).  2 New check: how often a full log analysis would point at our own code for each "
                        "cause.  3 Sample tickets: up to 20 tickets with their log lines, written as a user and a log "
                        "file would show them, with what each check should read. About 30-45 minutes; tickets can be short."),
        ("Leave out", "Real names, e-mail addresses, internal system names, credentials and real user data. "
                      "Everything can be invented, as in Part 1."),
        ("Cells", "Fill in YELLOW cells only. Grey rows are examples. Blue cells are headings."),
    ]
    for r, (a, b) in enumerate(rows, 1):
        ws.cell(r, 1, a).font = TITLE if r == 1 else BOLD
        ws.cell(r, 2, b).alignment = WRAP
    ws.column_dimensions["A"].width, ws.column_dimensions["B"].width = 18, 110

    # 1. Causes
    ws = wb.create_sheet("Causes")
    header(ws, "1. Your causes: code change and who is in charge",
           "Fixed by a code change = the remedy is a change to the application's code that a developer would review "
           "as a pull request (not a restart, rollback, data clean-up or database operation).",
           ["Cause ID", "Category", "Cause", "Remedy", "Fixed by a code change?", "Who is in charge (role, not a name)"],
           [10, 30, 50, 40, 18, 40])
    for k, value in enumerate(["EXAMPLE", "Authentication and access", "Expired service token",
                               "Renew the service token", "No", "Identity and access lead"], 1):
        ws.cell(5, k, value).fill = GREY
    for i, cause in enumerate(causes):
        row = 6 + i
        for k, value in enumerate([cause["id"], cause["category"], cause["name"], cause["remedy"]], 1):
            ws.cell(row, k, value).alignment = WRAP
        ws.cell(row, 5).fill = ws.cell(row, 6).fill = YELLOW
    dropdown(ws, ["Yes", "No"], f"E6:E{5 + len(causes)}")
    ws["E16"] = "If no cause is clear, escalate to (role):"
    ws["E16"].font = BOLD
    ws["F16"] = "Senior developer"
    ws["F16"].fill = YELLOW

    # 2. New check
    ws = wb.create_sheet("New check")
    ws["A1"], ws["A1"].font = "2. A new check: full log analysis (delegated to a language model)", TITLE
    ws["A2"] = ("The agent can choose to hand the full logs and stack traces to a language model with one question. "
                "Edit the wording if it is wrong; then rate it against each cause, as in Part 1.")
    for r, (label, value) in enumerate([("Check", d11["name"]), ("What it tests", d11["tests"]),
                                        ("A POSITIVE result means", d11["positive_means"]), ("Effort", d11["effort"])], 6):
        ws.cell(r, 1, label).font = BOLD
        ws.cell(r, 2, value).fill = YELLOW
        ws.cell(r, 2).alignment = WRAP
    dropdown(ws, ["Low", "Medium", "High"], "B9")
    ws["A12"] = "How likely is this check to be POSITIVE when the cause is present?"
    ws["A12"].font = BOLD
    for k, name in enumerate(["Cause ID", "Cause", "Rating"], 1):
        ws.cell(13, k, name).font, ws.cell(13, k).fill = BOLD, BLUE
    for i, cause in enumerate(causes):
        ws.cell(14 + i, 1, cause["id"])
        ws.cell(14 + i, 2, cause["name"])
        ws.cell(14 + i, 3).fill = YELLOW
    dropdown(ws, ratings, f"C14:C{13 + len(causes)}")
    ws.column_dimensions["A"].width, ws.column_dimensions["B"].width, ws.column_dimensions["C"].width = 24, 90, 16

    # 3. Sample tickets
    ws = wb.create_sheet("Sample tickets")
    check_cols = [f"{c['id']} {c['name']}" for c in checks] + [f"D11 {d11['name']}"]
    header(ws, "3. Sample tickets (up to 20)",
           "One incident per row. Write the ticket as a user would, and paste invented log lines in the format your "
           "logs use. Then say what each check would read from them: positive, negative, or not shown (the logs say "
           "nothing about it). See the Reference sheet for symptoms and checks.",
           ["Ticket ID", "Ticket text (as the user wrote it)", "Log lines (one per line)", "True cause",
            "Production?", "Priority", "Symptoms present (e.g. S01, S02)"] + check_cols,
           [10, 50, 70, 12, 12, 10, 18] + [14] * len(check_cols))
    example = ["EXAMPLE", "Approving results spins for about a minute and then fails. Live system.",
               "2026-11-03T08:10:00Z ERROR db lock wait timeout exceeded on marks\n"
               "2026-11-03T08:10:00Z INFO db oldest_tx_age=240s", "C02", "Yes", "High", "S01, S04"]
    example += ["not shown", "positive", "not shown", "not shown", "positive"] + ["not shown"] * (len(check_cols) - 5)
    for k, value in enumerate(example, 1):
        ws.cell(5, k, value).fill = GREY
        ws.cell(5, k).alignment = WRAP
    last = 5 + N_TICKETS
    for row in range(6, last + 1):
        ws.cell(row, 1, f"T{row - 5:02d}")
        for col in range(2, 8 + len(check_cols)):
            ws.cell(row, col).fill = YELLOW
            ws.cell(row, col).alignment = WRAP
    dropdown(ws, [c["id"] for c in causes] + ["None of these"], f"D6:D{last}")
    dropdown(ws, ["Yes", "No"], f"E6:E{last}")
    dropdown(ws, ["Low", "Medium", "High"], f"F6:F{last}")
    first, end = ws.cell(6, 8).column_letter, ws.cell(6, 7 + len(check_cols)).column_letter
    dropdown(ws, ["positive", "negative", "not shown"], f"{first}6:{end}{last}")
    ws.freeze_panes = "B6"

    # Reference
    ws = wb.create_sheet("Reference")
    ws["A1"], ws["A1"].font = "Reference: your symptoms and checks from Part 1", TITLE
    r = 3
    for title, items, fields in (("Symptoms", model["symptoms"], ("name", "reported_as")),
                                 ("Checks", checks + [d11], ("name", "positive_means"))):
        ws.cell(r, 1, title).font = BOLD
        r += 1
        for item in items:
            ws.cell(r, 1, item["id"])
            ws.cell(r, 2, item[fields[0]])
            ws.cell(r, 3, item[fields[1]])
            r += 1
        r += 1
    ws.column_dimensions["B"].width, ws.column_dimensions["C"].width = 50, 70

    OUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUT)
    print(OUT)


if __name__ == "__main__":
    main()
