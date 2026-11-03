# Artificial Intelligence Review submission package

| # | Deliverable | File |
|---|---|---|
| 1 | Flat LaTeX source (tex, cls, bst, bib, bbl, Fig1–3 .eps, with .pdf twins) and the compiled PDF | `Opol_AIR_source.zip`, `Opol_AIR_manuscript.pdf` (unzipped copy in `source/`) |
| 2 | Supplementary Information | `ESM/ESM_1.pdf` (Online Resource 1: Tables S1–S4), `ESM/ESM_2.xlsx` (Online Resource 2: audit files) |
| 3 | Requirements checklist (pass/fail) | `03_requirements_checklist.md` |
| 4 | Change log | `04_change_log.md` |
| 5 | Open questions | `05_open_questions.md` |
| 6 | Draft cover letter | `06_cover_letter_draft.md` |
| 7 | Text for the submission interface | `07_submission_interface_text.md` |
| – | Abstract, old vs new | `08_abstract_old_vs_new.md` |
| – | Verification report (recounts, checks) | `09_verification_report.md` |
| – | Re-use statements and overlap with the project report | `10_reuse_statement_and_overlap.md` |
| – | Standalone-framing proposals (not applied) | `11_framing_proposals.md` |

Rebuild everything from `research/slr/` (the source there is not modified):

```
cd outputs/submission/_build
python -I make_figures.py     ../../../research/slr ..
python -I build_manuscript.py ../../../research/slr ..
python -I make_esm.py         ../../../research/slr ..
cd ../source && ../../../tools/tectonic.exe manuscript.tex
python -I ../_build/check_order.py .. ; python -I ../_build/check_numbers.py ../../../research/slr ..
```

All edits to the text are literal pairs in `_build/edits.py`. Placeholders print as **[bold brackets]** (`\tbc{}`).
