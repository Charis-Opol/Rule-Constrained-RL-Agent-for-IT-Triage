# Systematic Literature Review: RL for Investigating, Acting and Escalating in IT Incident Triage

PRISMA 2020 systematic review supporting the RL incident-triage project. Searches run on 23 October 2026 (Scopus, ACM Digital Library, IEEE Xplore open access).

## Build

From this folder:

```
python -I audit/generate.py        # regenerate counts, tables, CSVs and references.bib
..\..\tools\tectonic.exe Opol_Charis_Systematic_Literature_Review.tex  # compile the PDF
```

`build.bat` at the repository root also builds this paper.

## Layout

| Path | Contents |
|---|---|
| `Opol_Charis_Systematic_Literature_Review.tex` | Document root (IEEEtran journal) |
| `sections/` | Abstract, Introduction, Methodology, Results, Discussion, Limitations, Future Research, Conclusion, AI declaration |
| `appendices/` | A: decision log for every report sought; B: study characteristics; C: coding of review-question elements; D: quality ratings |
| `figures/` | PRISMA flow diagram, coverage chart, ORCID icon |
| `tables/` | Hand-written abbreviations table; every other file here is **generated** (do not edit by hand) |
| `references.bib` | **Generated** from the Scopus export, the thesis bibliography and `audit/method_refs.bib` |
| `audit/review_data.py` | Single source of truth: full-text outcomes, extraction and quality coding for the 34 included studies, and the themes |
| `audit/generate.py` | Reads the screening record and `review_data.py`, asserts the PRISMA reconciliation, writes all generated files |
| `audit/*.csv` | `prisma_reconciliation`, `fulltext_decisions`, `exclusion_traceability`, `data_extraction`, `quality_appraisal`, `study_traceability`, `thematic_traceability` |

Inputs read by the generator: `../new-slr-exports/screening/title_abstract_screening.csv` and the raw Scopus export in `../new-slr-exports/` (raw exports and the full-text PDFs in `../new-slr-literature/` are git-ignored).

## PRISMA counts

4,399 identified; 73 duplicates and 4,195 removed by automation; 131 screened; 84 excluded; 47 sought; 7 not retrieved; 40 assessed; 6 excluded; 34 included. Citation searching was not carried out.

## Open items

- Verify the ORCID in `Opol_Charis_Systematic_Literature_Review.tex` (`\orcid` macro).
- Complete the `\todo` in `sections/ai_declaration.tex`.
- S108 has no full text and no recorded reason; S046 is a landing page only; five reports are closed access.
