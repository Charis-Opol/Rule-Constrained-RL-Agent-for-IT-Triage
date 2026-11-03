# Change log: IEEE manuscript → Artificial Intelligence Review submission

Scope: formatting, structure and compliance wording only. No result, count, percentage, table value, study classification, quality rating or conclusion changed. `_build/check_numbers.py` confirms it (see `09_verification_report.md`). The pipeline is reproducible:

```
python -I _build/make_figures.py   research/slr outputs/submission
python -I _build/build_manuscript.py research/slr outputs/submission
python -I _build/make_esm.py       research/slr outputs/submission
```

The source in `research/slr/` was **not modified**. The only new file there is `AIR_submission_guidelines.txt`, the saved guidelines page. The template ZIP was unzipped to a scratch copy and left untouched.

## Part 1: structural and global changes

| # | Before | After | Reason | Guideline satisfied |
|---|---|---|---|---|
| S1 | `\documentclass[journal]{IEEEtran}`, fontspec + TeX Gyre Termes, TikZ/pgfplots, cite | `\documentclass[pdflatex,sn-basic]{sn-jnl}`, template packages plus booktabs, array, tabularx, longtable; no custom fonts | Springer template, Basic style with author-year citations; no `Numbered` option | Text: Springer Nature LaTeX template; template manual §3.2 (no custom fonts) |
| S2 | Many files in `sections/`, `tables/`, `figures/`, `appendices/` | A single `manuscript.tex`; the count macros (`\NIncluded` and so on) replaced with their values; every row file inlined | Flat folder, robust compile | LaTeX and Online Submission: no subfolders |
| S3 | Author line with registration number and student e-mail, ORCID icon | `\author*`, `\affil*` (department, faculty, institution, city [TBC], state [TBC], country), two e-mails, ORCID as text | Title page fields; the class `\orcid` needs an `Orcidlogo.eps` that isn't in the package | Title Page: author information |
| S4 | No acknowledgements | `\bmhead{Acknowledgements}` immediately after the title block (placeholder) | Acknowledgements on the title page | Acknowledgments |
| S5 | Abstract of 357 words | 246 words; IT and PRISMA defined; no citations (`08_abstract_old_vs_new.md`) | Length and abbreviations | Abstract |
| S6 | 11 "Index Terms" | 6 keywords (provisional, awaiting confirmation) | 4–6 keywords | Keywords |
| S7 | Roman section numbers; run-in themes `\emph{1) …}` (a fourth level) | Decimal 1 / 1.1 / 1.1.1; the 18 run-in themes became `\subsubsection`s with the same words (number and final full stop removed) | At most three levels | Headings |
| S8 | `\cite{…}` numbered [n] | natbib author-year: 92 `\citet` (author named in the sentence, e.g. "Chen et al. (2020) describe…", possessives as "Singh's (2026) guard") and the rest `\citep` "(A 2020; B 2021)". Table list cells use `\citealp`. The authors' names are no longer repeated next to a number. | Name-year citation | References: Citation |
| S9 | Plain "Sahin and Mert" in the text | "Şahin and Mert" (`\c{S}`), matching the reference list | Consistent spelling | Abbreviations / consistency |
| S10 | "as Turan et al. argue" | "as Turan (2026) argues" | arXiv:2606.08919 has a single author (checked on arXiv); a citation error, not a finding | References: accuracy |
| S11 | `references.bib` (56 entries, including uncited `hammar2026llm`) | 55 cited entries plus `opol2026data` (dataset, placeholder DOI). DOIs moved from `url` to `doi` and printed as https://doi.org/…; journal titles abbreviated per the ISSN LTWA only where certain; conference names written out; "Art. no." given as the page/article number in Springer style; `jaber2025` spurious `number = {2025}` dropped; Şahin encoded `{\c{S}}ahin` for alphabetical sorting | Springer reference style; only cited works; data citation | Reference list; Data citation |
| S12 | Tables I–XXII (Roman); Table I never cited; VI cited before V; IX cited before VIII; XVII cited in the Methods before VIII–XVI | Tables 1–15 (Arabic), first cited in order 1…15: a sentence citing Table 1 added; the extraction-table pointer in Sect. 2.2 changed to "Section 2.7"; the reconciliation table moved ahead of the reasons table; the traceability pointer in Sect. 2.9 changed to "Section 3.10" | Consecutive citation | Tables |
| S13 | IEEE Title Case captions | Captions rewritten to explain each table's columns (no content change) | Captions explaining components | Tables |
| S14 | Note line under the characteristics table | Footnote with superscript "a" beneath the table body (`\footnotetext`) | Table footnotes | Tables; Footnotes |
| S15 | `table*` two-column floats sized for an 18 cm text block | Single-column `table` sized to the 13.1 cm text block; the traceability table (now about 2.5 pages because of author-year citations) set as a `longtable` with the same number and caption | Template layout | Text |
| S16 | Abbreviations table I (17 rows) | Table 1: rows kept, 5 added (IDS, IoT, IT, OT, ROC-AUC) because the text now uses and defines them; sorted alphabetically. **Not removed**: awaiting your decision. | Consistency of abbreviations | Abbreviations |
| S17 | TikZ PRISMA figure, pgfplots bar chart, TikZ evidence diagram, all drawn in the PDF | `Fig1.eps`, `Fig2.eps`, `Fig3.eps`: vector, Arial 8 pt embedded (Type 42), 0.6 pt lines, greyscale with value labels and a hatched box, drawn at final size from the same count files. Fig. 3's citations moved from the artwork into the caption. PDF twins for local compilation. | Artwork specification and accessibility | Artwork and Illustrations |
| S18 | Figure captions ending with a full stop, "Figure"/"Fig." | Descriptive captions identifying every element, with no closing punctuation; the class prints **Fig. N**; "Fig.~\ref" in the text | Figure captions; accessibility | Figure Captions; Accessibility |
| S19 | Appendices A–D in the article (one-column longtables) | Moved to **Online Resource 1** (`ESM_1.pdf`) as Tables S1–S4, rows unchanged, with the article title, journal, author, affiliation and e-mail at the top and their own reference list. Every "Appendix X" pointer became "Table SX of Online Resource 1". | Your choice (Q: Appendices); SI rules | Supplementary Information |
| S20 | Audit CSV files only in the repository folder | **Online Resource 2** (`ESM_2.xlsx`): seven CSVs, one per worksheet, unchanged, plus a README sheet with the required header information and captions | SI spreadsheets; data sharing | Supplementary Information; Research Data Policy |
| S21 | "Declaration of AI Assistance" section at the end; separate AI sentences in Sects II-E and II-H | One Methods subsection, **2.11 Use of an AI Assistant**: a factual list of what was done with and without the assistant. It keeps "None of the decisions … was independently duplicated, and no measure of agreement was computed" and adds an accountability sentence. Sects 2.5 and 2.8 point to it, and the Screening sentence on no duplication is **kept verbatim**. Model version, period and the manuscript-preparation sentence are marked [TBC]. | LLM use documented in the Methods; human accountability | Title Page (LLM paragraph) |
| S22 | No declarations | "Statements and Declarations" before the references: Funding [TBC], Competing interests [TBC], Ethics approval and consent (not applicable, with reason), Consent for publication (not applicable), Data availability, Materials and code availability, Author contributions, Use of AI tools (pointer to Sect. 2.11), Prior dissemination and re-use of material [TBC] | Mandatory statements | Statements and Declarations; Competing Interests; Research Data Policy; Ethical Responsibilities (text recycling) |
| S23 | No SI section | `\bmhead{Supplementary information}` with a concise caption for each Online Resource | SI captions | Supplementary Information: Captions |
| S24 | Non-ASCII characters in report titles (– ’) | ASCII TeX equivalents (`--`, `'`) | Safe pdflatex compile | LaTeX and Online Submission |

**Deliberately not changed (awaiting your approval):** all passages that refer to "the project", "Chapter Two", "the thematic review", "the planned agent" and "RQ1–RQ5" (see `11_framing_proposals.md`); the possible clarifying notes on 20 vs 19 and on "about a third" (see `09_verification_report.md`); and Table 1's existence.

## Part 2: literal text edits (generated from `_build/edits.py`)

Each edit below was applied exactly once. The build stops if any `Before` string is not found exactly once.

