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

| # | Section | Before | After | Reason (guideline) |
|---|---|---|---|---|
| E1 | introduction | `\section{Introduction}` | `\section{Introduction}\label{sec:intro}` | Label for cross-references from the declarations |
| E2 | introduction | `\IEEEPARstart{O}{rganisations} depend on IT services` | `Organisations depend on information technology (IT) services` | IEEEtran drop cap removed; IT defined at first mention (guideline: abbreviations) |
| E3 | introduction | `In both descriptions, triage is a set of decisions made before the cause of the incident is known.` | `In both descriptions, triage is a set of decisions made before the cause of the incident is known. The abbreviations used in this review are listed in Table~\ref{tab:abbrev}. %%TABLE:abbrev%%` | Table 1 was never cited in the text; citation added so tables are cited in order (guideline: tables) |
| E4 | introduction | `is listed in Appendix~\ref{app:decisionlog}` | `is listed in Table~S1 of Online Resource~1` | Appendix A moved to Supplementary Information, cited as Online Resource (guideline: SI numbering) |
| E5 | introduction | `The review addresses five questions:` | `The review addresses five systematic review questions (SRQ1--SRQ5):` | SRQ defined at first mention (guideline: abbreviations) |
| E6 | introduction | `formulated as MDP, POMDP or RL problems` | `formulated as Markov decision process (MDP), POMDP or RL problems` | MDP defined at first mention (guideline: abbreviations) |
| E7 | methodology | `\section{Methodology (PRISMA Protocol)}` | `\section{Methods}` | Heading aligned with the guideline wording, which requires LLM use to be documented in the Methods section |
| E8 | methodology | `reported according to the PRISMA 2020 guideline` | `reported according to the Preferred Reporting Items for Systematic Reviews and Meta-Analyses (PRISMA) 2020 guideline` | PRISMA defined at first mention (guideline: abbreviations) |
| E9 | methodology | `where much AIOps work appears` | `where much work on artificial intelligence for IT operations (AIOps) appears` | AIOps defined at first mention (guideline: abbreviations) |
| E10 | methodology | `as data items in the extraction form (Table~\ref{tab:extraction}).` | `as data items in the extraction form (Section~\ref{sec:extraction}).` | Table 6 was cited before Table 5; pointer changed to the section so tables are cited in order (guideline: tables) |
| E11 | methodology | `The criteria in Table~\ref{tab:criteria} were written before screening` | `The inclusion criteria (IC1--IC5) and exclusion criteria (EC1--EC7) in Table~\ref{tab:criteria} were written before screening` | IC and EC defined at first mention (guideline: abbreviations) |
| E12 | methodology | `The title and abstract decisions and the full-text assessments of the reports on file were made with an AI assistant, and two full-text decisions were made manually (Section~\ref{sec:results}).` | `The title and abstract decisions and the full-text assessments of the reports on file were made with the AI assistant described in Section~\ref{sec:ai}, and two full-text decisions were made manually (Section~\ref{sec:re ...` | Points to the single account of AI use in the Methods (guideline: LLM use documented in Methods) |
| E13 | methodology | `are listed in Appendix~\ref{app:decisionlog}.` | `are listed in Table~S1 of Online Resource~1.` | Appendix A moved to Supplementary Information (guideline: SI numbering) |
| E14 | methodology | `\subsection{Data Extraction}` | `\subsection{Data Extraction}\label{sec:extraction}` | Label for the section cross-reference that replaces the out-of-order table citation |
| E15 | methodology | `The ratings were made with the AI assistance declared at the end of this paper and have not been independently checked.` | `The ratings were made with the AI assistant described in Section~\ref{sec:ai} and have not been independently checked.` | Points to the single account of AI use in the Methods (guideline: LLM use documented in Methods) |
| E16 | methodology | `the full mapping is given in Table~\ref{tab:trace} and in the traceability files that accompany this review.` | `the full mapping is given in Section~\ref{sec:trace} and in the traceability files in Online Resource~2.` | Table 15 was cited before Tables 8 to 14; pointer changed to the section (guideline: tables); audit files cited as Online Resource 2 |
| E17 | methodology | `The review is accompanied by a set of audit files:` | `The review is accompanied by a set of audit files (Online Resource~2; see also the data availability statement):` | Audit files cited as Supplementary Information and linked to the Data Availability statement |
| E18 | methodology | `The tables and counts in this paper are generated from these files.` | `The tables and counts in this paper are generated from these files. \subsection{Use of an AI Assistant}\label{sec:ai} An AI assistant, Claude (Anthropic) \tbc{model version and period of use}, was used in conducting this ...` | Single factual account of LLM use in the Methods, replacing the end-of-paper declaration; limitation kept (guideline: LLM use documented in Methods; human accountability) |
| E19 | results | `Figure~\ref{fig:prisma} shows the flow` | `Fig.~\ref{fig:prisma} shows the flow` | Springer figure citation style |
| E20 | results | `%%TABLE:tareasons%% %%TABLE:reconcile%%` | `%%TABLE:reconcile%% %%TABLE:tareasons%%` | Reconciliation table is cited before the reasons table, so it now comes first (guideline: tables cited in order) |
| E21 | results | `\input{figures/prisma_flow}` | `%%FIGURE:prisma%%` | Fig. 1 now an EPS file (guideline: artwork) |
| E22 | results | `\input{figures/fig_coverage}` | `%%FIGURE:coverage%%` | Fig. 2 now an EPS file (guideline: artwork) |
| E23 | results | `Appendix~\ref{app:decisionlog} gives the outcome for every report sought.` | `Table~S1 of Online Resource~1 gives the outcome for every report sought.` | Appendix A moved to Supplementary Information |
| E24 | results | `and Appendix~\ref{app:characteristics} describes each one.` | `and Table~S2 of Online Resource~1 describes each one.` | Appendix B moved to Supplementary Information |
| E25 | results | `alert triage in security operations centres,` | `alert triage in security operations centres (SOCs),` | SOC defined at first mention (guideline: abbreviations) |
| E26 | results | `industrial and IoT systems` | `industrial and Internet of Things (IoT) systems` | IoT defined at first mention (guideline: abbreviations) |
| E27 | results | `chiefly the CAGE-2 and CAGE-4 cyber-defence gyms` | `chiefly the CAGE-2 and CAGE-4 cyber-defence gyms (Cyber Autonomy Gym for Experimentation)` | CAGE defined at first mention (guideline: abbreviations) |
| E28 | results | `Appendix~\ref{app:quality} gives every rating.` | `Table~S4 of Online Resource~1 gives every rating.` | Appendix D moved to Supplementary Information |
| E29 | results | `Appendix~\ref{app:coverage} records the elements study by study.` | `Table~S3 of Online Resource~1 records the elements study by study.` | Appendix C moved to Supplementary Information |
| E30 | results | `against 6.1 for a plain DQN` | `against 6.1 for a plain deep Q-network (DQN)` | DQN defined at first mention (guideline: abbreviations) |
| E31 | results | `from $O(N^2)$ to $O(1)$` | `from $\mathrm{O}(N^{2})$ to $\mathrm{O}(1)$` | Upright operator, italic variable (guideline: scientific style) |
| E32 | results | `(142~s to 144~s)` | `(142\,s to 144\,s)` | SI unit spacing (guideline: SI units) |
| E33 | results | `than an unshielded PPO agent` | `than an unshielded proximal policy optimisation (PPO) agent` | PPO defined at first mention (guideline: abbreviations) |
| E34 | results | `through accuracy, reward, cost, recall or MCC,` | `through accuracy, reward, cost, recall or the Matthews correlation coefficient (MCC),` | MCC defined at first mention (guideline: abbreviations) |
| E35 | results | `whose failure F1 and ROC-AUC concealed and MCC revealed` | `whose failure the F1 score and the area under the receiver operating characteristic curve (ROC-AUC) concealed and MCC revealed` | ROC-AUC defined at first mention (guideline: abbreviations) |
| E36 | results | `rose from 41.2~s to 79.4~s at peak load` | `rose from 41.2\,s to 79.4\,s at peak load` | SI unit spacing (guideline: SI units) |
| E37 | results | `in about 15 to 19 seconds, against more than 30 minutes for PPO` | `in about 15\,s to 19\,s, against more than 30\,min for PPO` | SI unit symbols (guideline: SI units) |
| E38 | results | `\subsection{Thematic Traceability}` | `\subsection{Thematic Traceability}\label{sec:trace}` | Label for the section cross-reference from the Methods |
| E39 | discussion | `as Turan et al.\ argue it should be~\cite{turan2026}` | `as Turan argues it should be~\cite{turan2026}` | Citation error: arXiv:2606.08919 has a single author (E. Turan), so "et al." was wrong |
| E40 | limitations | `Section~\ref{sec:screening} and Appendix~\ref{app:decisionlog} state` | `Section~\ref{sec:screening} and Table~S1 of Online Resource~1 state` | Appendix A moved to Supplementary Information |

## Part 3: citations converted to textual form (\citet)

Key and the author mention it replaced, in document order:

```
chen2020	Chen et al.\
chen2020	Chen et al.\
remil2024	Remil et al.\
chen2020	Chen et al.\
remil2024	Remil et al.\
remil2024	Remil et al.\
kitchenham2007	Kitchenham and Charters
alauthman2026	Alauthman et al.
hammar2025	Hammar and Li
hammar2026belief	Hammar et al.
wang2023hrlhf	Wang et al.
ding2023	Ding et al.
ren2025	Ren et al.
dunsin2025	Dunsin et al.
ren2025	Ren et al.
alauthman2026	Alauthman et al.
hammar2026belief	Hammar et al.
sahin2026	Sahin and Mert
nyberg2024	Nyberg and Johnson
peralta2025	Peralta et al.
okafor2026	Okafor
rojasrodriguez2026	Rojas Rodriguez et al.
ghanem2026	Ghanem et al.
hammar2025	Hammar and Li
kovtun2026	Kovtun et al.
hammar2026belief	Hammar et al.\
hammar2025	Hammar and Li
kovtun2026	Kovtun et al.\
koupaei2026	Koupaei and Demirkol
koupaei2026	Koupaei and Demirkol
contractor2025	Contractor et al.\
sahin2026	Sahin and Mert
wu2026	Wu et al.\
peralta2025	Peralta et al.\
wang2023hrlhf	Wang et al.\
wu2026	Wu et al.\
kovtun2026	Kovtun et al.\
ghanem2026	Ghanem et al.\
wang2023hrlhf	Wang et al.\
bhosale2026	Bhosale et al.\
alturkistani2022	Alturkistani and El-Affendi
sahin2026	Sahin and Mert's
kovtun2026	Kovtun et al.'s
okafor2026	Okafor
singh2026	Singh
koupaei2026	Koupaei and Demirkol
okafor2026	Okafor's
sahin2026	Sahin and Mert
kovtun2026	Kovtun et al.\
contractor2025	Contractor et al.\
kovtun2026	Kovtun et al.\
sahin2026	Sahin and Mert
ravi2025	Ravi et al.\
singh2026	Singh
koupaei2026	Koupaei and Demirkol
elicha2026	Elicha and Lopez
okafor2026	Okafor
ravi2025	Ravi et al.'s
singh2026	Singh's
ravi2025	Ravi et al.\
singh2026	Singh
sahin2026	Sahin and Mert
singh2026	Singh's
ravi2025	Ravi et al.'s
kovtun2026	Kovtun et al.
peralta2025	Peralta et al.\
okafor2026	Okafor
ravi2025	Ravi et al.'s
sahin2026	Sahin and Mert
peralta2025	Peralta et al.'s
aenugu2026	Aenugu's
nyberg2024	Nyberg and Johnson's
hammar2025	Hammar and Li's
hammar2026belief	Hammar et al.'s
sahin2026	Sahin and Mert
kovtun2026	Kovtun et al.\
contractor2025	Contractor et al.\
chen2020	Chen et al.'s
sahin2026	Sahin and Mert
sahin2026	Sahin and Mert's
kovtun2026	Kovtun et al.'s
turan2026	Turan
singh2026	Singh's
ravi2025	Ravi et al.'s
alshiekh2018	Alshiekh et al.\
kovtun2026	Kovtun et al.
sahin2026	Sahin and Mert's
sahin2026	Sahin and Mert
alauthman2026	Alauthman et al.
sahin2026	Sahin and Mert
kovtun2026	Kovtun et al.
sahin2026	Sahin and Mert
```
