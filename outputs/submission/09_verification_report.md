# Verification report

All checks were run on the final build (`source/manuscript.tex`, `manuscript.pdf`, `ESM/`). No data were changed. Where a check found an inconsistency in the original, it is reported here and **left as it was** for you to decide.

## 1. Compilation

| Check | Result |
|---|---|
| Engine | Tectonic 0.17.0 (XeTeX + BibTeX), per your choice. **pdflatex + bibtex were not run locally.** |
| Errors | 0 |
| Undefined references or citations | 0 / 0 |
| Missing files (.cls, .bst, figures) | none: `sn-jnl.cls`, `sn-basic.bst`, `references.bib`, Fig1–3 are all in the flat folder |
| Bibliography | 56 items = 55 cited works + 1 dataset; every .bib entry is cited, and no citation lacks an entry |
| Warnings | One overfull line of 0.73 pt (Fig. 1 caption), which is invisible. The rest are routine underfull vbox and bookmark-level notices. |
| Pages | Manuscript 38; ESM_1 13 |

**Before you submit:** Editorial Manager will compile the ZIP with pdflatex and show you the PDF to approve. Check that PDF against `Opol_AIR_manuscript.pdf`, especially the reference list and Fig. 1. If you want a local pdflatex run first, Overleaf (upload the ZIP, set the compiler to pdfLaTeX) or a MiKTeX install will do it.

## 2. PRISMA flow, recounted

| Stage | n | Arithmetic | OK |
|---|---|---|---|
| Identified | 4399 | 3394 (Scopus) + 1000 (ACM) + 5 (IEEE) = 4399 | ✓ |
| After duplicates | 4326 | 4399 − 73 = 4326 | ✓ |
| Removed by automation | 4195 | 1462 (type) + 32 (year) + 2270 (block A) + 431 (block B) = 4195; and 2270 + 431 = 2701 (the "string blocks" line in Fig. 1) | ✓ |
| Screened | 131 | 4326 − 4195 = 131 | ✓ |
| Excluded at title/abstract | 84 | Table 9: 22+19+12+11+9+3+2+2+2+1+1 = 84 | ✓ |
| Sought | 47 | 131 − 84 = 47; priority groups 25 + 22 = 47 | ✓ |
| Not retrieved | 7 | 6 (closed access or abstract only) + 1 (no record) = 7; Table 10 lists 7 | ✓ |
| Assessed | 40 | 47 − 7 = 40 | ✓ |
| Excluded at full text | 6 | 3 + 1 + 1 + 1 = 6; Table 11 lists 6 | ✓ |
| Included | 34 | 40 − 6 = 34; priority groups 20 + 14 = 34 | ✓ |

The numbers in Fig. 1 (new EPS), Table 8 and the text all come from the same `counts.tex`, and they agree.

## 3. Table totals, recounted

| Table | Check | OK |
|---|---|---|
| 12 Characteristics | Setting 10+6+11+5+2 = 34; Year 1+2+2+2+10+17 = 34; Environment 6+13+5+1+6+3 = 34; Formulation overlaps by design (footnote a) | ✓ |
| 13 Quality summary | Each row Met + Part + Not = 34 (Q1 25+9+0, Q2 19+14+1, Q3 19+8+7, Q4 21+10+3, Q5 11+7+16, Q6 9+10+15, Q7 19+7+8, Q8 5+17+12); identical to the per-study ratings in Table S4 and `quality_appraisal.csv` | ✓ |
| 14 Coverage | Constraint categories 5+6+4+11+8 = 34 (mutually exclusive); the counts equal the Fig. 2 bars (same source file) | ✓ |
| S4 Quality ratings | Number meeting ≥6 items = 9 (= "9 meet at least six"); number meeting ≤2 = 12 (= "12 meet at most two") | ✓ |
| Text and abstract | 4 belief, 17 information gathering, 7 escalation, 1 all three, 5 shield, 3 blocked, 31 decision quality, 5 escalation measured, 4 compliance, 15 robustness, 27 recent, 17 in 2026, 2020 earliest | ✓ (from the same macros) |

## 4. The items you asked me to verify

**(a) "20 studies have a non-learning baseline" vs Table 13 (formerly XIII), "Q3 met = 19".** Not an arithmetic error. The two counts use different criteria:

- In the extraction (`data_extraction.csv`, `rule_baseline = True`), 20 studies compare with a non-learning policy.
- Q3 is rated *met* only when that policy "is evaluated in the same environment".
- The one study counted in the first but not the second is **Dunsin et al. (2025)**. Its non-learning comparison is "time taken by a human forensic expert", and its Q3 is rated **Part**.

The text already says both "20 studies compare against a non-learning policy" (Sect. 3.8.2) and "A non-learning baseline is more common, met by 19" (Sect. 3.3). If you want the difference explained, a possible note (not applied) for Sect. 3.3: *"(the twentieth, Dunsin et al. 2025, compares with a human expert's time outside the study's environment, so Q3 is rated partly met)"*.

**(b) "Items met" in Table 22 (now S4).** Consistent. For all 34 studies, "Items met" equals the number of **Yes** ratings; Part ratings are not counted. This holds in the PDF table and in `quality_appraisal.csv`. Rows that look low have many Part ratings: Aenugu has 1 Yes and 6 Part, so 1 item met, and Singh has 1 Yes and 5 Part. This was already stated in the appendix note and is now also in the Table S4 header: "Items met counts only the items rated Yes; items rated Part are not counted."

## 5. Other inconsistencies found in the original (not changed)

1. **Table 15, SRQ5 row 1, interpretation:** "Robustness is tested in about a third of studies", but the count is 15 of 34 (44%), and the text says "under half the studies" (Sect. 3.9). A possible fix: "in under half of the studies".
2. **Table 15, SRQ5 row 1, supporting studies:** 11 studies are cited, while 15 studies are counted as testing robustness. The four not named are in `data_extraction.csv` (robustness column). This may be intended, since the theme names illustrative studies, but a reader comparing the table with the count will notice.
3. **Table 15, SRQ1 row 3, and Sect. 3.5.3:** "In about half the studies the state is a vector…" cites 15 studies, which is 44%. Acceptable as "about half", noted only for consistency with item 1.
4. **Turan (2026)** was written as "Turan et al." in Sect. 4.2. arXiv lists one author. This was **corrected**, as a citation error rather than a finding (change log S10).
5. **Ren et al. (2025)** is cited as a known relevant study that the search missed. That's consistent with the limitations; nothing to change.

## 6. Citation order and abbreviations (script: `_build/check_order.py`)

- Tables: first text citations in the order 1, 2, …, 15: **PASS**.
- Figures: 1, 2, 3: **PASS**.
- Abbreviations: every abbreviation used in the body is defined at first use (IT, RL, POMDP, MDP, SRQ, SO, PRISMA, AIOps, IC, EC, SOC, CAGE, IoT, DQN, PPO, MCC, ROC-AUC). **Exception:** RQ1–RQ5 in Table 2 are explained only by the column heading, pending the framing decision.
- Table 1 lists five abbreviations that the text never uses: CMDP, ICS, LLM, MTTR and RCA. This matters for the keep-or-remove decision (see `05_open_questions.md`).

## 7. Number preservation (script: `_build/check_numbers.py`)

Every number printed in the original body was compared with every number printed in the new body, including the text drawn into the new Fig. 1 and Fig. 2. The remaining differences all come from new wording or removed labels, not data:

- **Removed:** the run-in theme labels "1)" to "4)"; the TikZ/pgfplots drawing parameters; "S038" (excluded from the comparison).
- **Added:** "131" in the new Sect. 2.11 ("all 131 screened records"); "34" in three new table captions ("the 34 included studies"); "2020" in "PRISMA 2020 flow diagram" (Fig. 1 caption); "Online Resource 1/2" and "Table S1–S4" pointers.

**No count, percentage, table value, classification or rating differs.**

## 8. Figures

| File | Format | Size | Fonts | Lines | Colour |
|---|---|---|---|---|---|
| Fig1.eps | EPSF-3.0 | 131 × 150 mm (text width) | ArialMT, Arial-BoldMT, Type 42, embedded | 0.6 pt | greyscale; stage bars #e6e6e6 with black text (contrast ≈ 16.8:1) |
| Fig2.eps | EPSF-3.0 | 120 × 78 mm | ArialMT embedded | 0.6 pt | one grey series with a value label on every bar; labels on white |
| Fig3.eps | EPSF-3.0 | 120 × 72 mm | ArialMT, Arial-BoldMT embedded | 0.6 pt and 1.2 pt | grey boxes; conclusion box hatched (a pattern, not colour) |

All lettering is 8 pt. The figures are included at natural size, so the 8 pt is the final size.
