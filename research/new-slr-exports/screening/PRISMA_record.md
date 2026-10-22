# PRISMA 2020 record: identification and title/abstract screening

Screening run: 23 October 2026. Exports dated 22 October 2026 (`research/new-slr-exports/`, not tracked).
Reproduce with `python -I prisma_pipeline.py <exports dir> <out dir>`; the screening decisions are in `title_abstract_screening.csv`.

## Counts

| Stage | Records |
|---|---|
| **Identified** | **4,399** (Scopus 3,394; ACM DL 1,000; IEEE Xplore 5) |
| Duplicates removed (DOI, then normalised title) | 73 |
| Records after de-duplication | 4,326 |
| Removed by automation: document type outside protocol (reviews, books, chapters, ACM proceedings front matter, notes) | 1,462 |
| Removed by automation: published outside 2015–2026 | 32 |
| Removed by automation: no method term (block A) in title/abstract/keywords | 2,270 |
| Removed by automation: no setting term (block B) in title/abstract/keywords | 431 |
| **Records screened (title and abstract)** | **131** |
| Records excluded at title/abstract | 84 |
| **Reports sought for retrieval** | **47** (25 priority 1, 22 priority 2) |

Title/abstract exclusions by first failed criterion:

| Code | Reason | n |
|---|---|---|
| EC1 | Not a computing incident (traffic, emergency, medical, police, finance) | 22 |
| IC1 | RL is not the method under study (unspecified component of a larger framework, or RL used only to train a model) | 19 |
| EC6 | Secondary study, position paper or workshop summary | 12 |
| EC2 | Resource management only | 11 |
| EC3 | Detection or classification only | 9 |
| IC4 | No quantitative evaluation | 3 |
| IC3 | No triage-relevant decision | 2 |
| EC5 | LLM agent without an RL policy | 2 |
| EC7 | Earlier version of an included study | 2 |
| IC2 | Not incident handling (predictive maintenance) | 1 |
| EC4 | Offensive security | 1 |
| | **Total** | **84** |

## Deviations from the protocol (report these in the method section)

1. **The protocol string was applied locally.** The exports contain records that the field-restricted string could not have returned: 1,462 records of excluded types, and 630 ACM entries that are whole proceedings volumes, which means a full-text search. The protocol string, in blocks A and B, was therefore run over the title, abstract and keywords of every exported record. Records without an abstract were checked by title: four were removed and none was in scope.
2. **Block C was dropped.** It excluded two in-scope benchmark studies (Hammar & Li 2025, S094; Hammar et al. 2026, S015), whose abstracts use none of its terms. Dropping it added 30 records to screening.
3. **Interpretation of IC1.** A record was excluded under IC1 when the abstract named RL only as one unspecified part of a multi-technique framework, or used RL only to fine-tune a model (an LLM or a summariser) and not as a decision policy. Where the role of RL was unclear, the record was kept for full-text screening.
4. **Interpretation of IC3.** Root cause analysis in which RL decides what to examine next (graph exploration, pruning or stopping) counts as a diagnostic, information-gathering decision.

## Known gaps in identification

- **IEEE Xplore returned 5 records.** The search or the export was incomplete. Re-run the IEEE string and export all results (CSV, with abstracts), then re-run the pipeline.
- **The ACM export holds exactly 1,000 records**, the ACM export limit. Re-run with *Search within: Title, Abstract, Author Keywords* so the result fits under the limit.
- **Benchmark studies not retrieved:** Ren et al. 2025 (ARCS) is not in the Scopus export. Kim & Dán 2025 and Hammar et al. 2026 (LLM planner) are present but fail block A (no RL or MDP term), as expected. Treat these through snowballing.

## Single-reviewer screening

All decisions were made by one screener (AI-assisted, then checked by the author). Before full-text screening, a second person should independently screen a random 20% (about 26 records) and report Cohen's kappa.
