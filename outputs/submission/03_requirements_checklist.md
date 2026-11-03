# Requirements checklist: Artificial Intelligence Review submission

Authority: the journal's *Submission guidelines* page (https://link.springer.com/journal/10462/submission-guidelines), retrieved 3 November 2026 and saved as `research/slr/AIR_submission_guidelines.txt`. The file named in the brief was not in the project. Supporting sources: the Springer Nature LaTeX template (December 2024) and its `user-manual.pdf`.

Status key: **PASS** = met and checked. **PENDING** = done, but waiting on something only you can supply (see `05_open_questions.md`). **FLAG** = needs your decision. **N/S** = the guidelines don't specify this.

## A. Manuscript submission and title page

| # | Requirement (source) | Status | Evidence / note |
|---|---|---|---|
| A1 | Not published before and not under consideration elsewhere (Manuscript Submission) | PENDING | Stated in the draft cover letter. You confirm it at submission. |
| A2 | Editable source files and a compiled PDF (Source Files; Text Formatting) | PASS | `Opol_AIR_source.zip` and `Opol_AIR_manuscript.pdf` |
| A3 | Author contributions and competing interests entered in the submission interface; only that version is published (Submitting Declarations) | PENDING | Draft wording in `07_submission_interface_text.md` |
| A4 | No authorship changes after submission (Please note) | PASS | Sole author: Charis Opol |
| A5 | Title concise and informative (Title Page) | PASS | Unchanged from the original |
| A6 | Author name(s) | PASS | `\author*{Charis Opol}` |
| A7 | Affiliation as institution, (department), city, (state), country | PENDING | Department, faculty, university and country are filled in. **City** and the optional **state/region** are placeholders. |
| A8 | Corresponding author clearly indicated, with an active e-mail | PASS | Marked with `*`. Two addresses, as you asked: B29654@students.ucu.ac.ug and charisopol@gmail.com |
| A9 | 16-digit ORCID, if available | PENDING | 0009-0003-7417-7984 (16 digits) is printed below the title block. The repo README flags it "to verify". Please confirm. |
| A10 | LLMs are not authors; LLM use documented in the Methods; human accountability (Title Page) | PENDING | New Methods Sect. 2.11 "Use of an AI Assistant" is the single account. It keeps the "not independently duplicated" limitation and adds an accountability sentence. Model version and period of use still to supply. |
| A11 | Abstract 150–250 words, no undefined abbreviations, no unspecified references | PASS | 246 words, no citations. IT and PRISMA are defined; RL, POMDP and SOC are not used. See `08_abstract_old_vs_new.md`. |
| A12 | 4–6 keywords | PENDING | Six proposed and set provisionally; awaiting your confirmation |
| A13 | "Statements and Declarations" section; submissions without it are returned (Title Page; Competing Interests) | PENDING | Present before the reference list. Funding and competing-interest wording await your answers. |

## B. Text

| # | Requirement | Status | Evidence / note |
|---|---|---|---|
| B1 | LaTeX, Springer Nature template recommended (Text) | PASS | `sn-jnl.cls`, `[pdflatex,sn-basic]` options (Basic style, author-year; no `Numbered`) |
| B2 | Decimal headings, at most three levels (Headings) | PASS | Roman numerals replaced with 1, 1.1 and 1.1.1. The run-in themes "1) 2) 3)" are now level-3 headings (for example, 3.5.1). Nothing goes below level 3. |
| B3 | Abbreviations defined at first mention and used consistently (Abbreviations) | PASS (one FLAG) | Checked by script (`_build/check_order.py`). Definitions were added for IT, MDP, SRQ, PRISMA, AIOps, IC/EC, SOC, CAGE, IoT, DQN, PPO, MCC, ROC-AUC and OT. **FLAG:** RQ1–RQ5 in Table 2 belong to the project framing and await your framing decision. |
| B4 | Footnotes: not citation-only, no bibliographic details, no figures or tables; table footnotes use lower-case letters; never endnotes (Footnotes) | PASS | No text footnotes. One table footnote (Table 12), marked "a" and placed beneath the table body. No endnotes. |
| B5 | Acknowledgements in a separate section on the title page; funders named in full (Acknowledgments) | PENDING | Placed straight after the title block, before the Introduction. Because the abstract fills page 1, it prints at the top of page 2; production re-sets the layout anyway. Content is a placeholder. |
| B6 | No subfolders in the LaTeX submission (LaTeX and Online Submission) | PASS | The ZIP is flat. |
| B7 | SI units (Scientific style) | PASS | "15 to 19 seconds" became 15 s to 19 s, and "30 minutes" became 30 min. Thin spaces were added before s in three places. |
| B8 | Italic single-letter variables, upright operators (Scientific style) | PASS | $\mathrm{O}(N^{2})$ and $\mathrm{O}(1)$ use an upright O with an italic N. *n* is italic in Table 8. |

## C. References

| # | Requirement | Status | Evidence / note |
|---|---|---|---|
| C1 | Name-year citations in parentheses (Citation) | PASS | 92 textual citations converted to `\citet` (for example, "Chen et al. (2020) describe") and the rest to `\citep`. natbib suffixes a/b automatically. No same-author/same-year pair remains among the cited works. |
| C2 | Only cited works; published or accepted only (Reference list) | FLAG | 55 cited works plus 1 dataset; the uncited `hammar2026llm` was removed. **FLAG:** three arXiv preprints (Remil et al. 2024; Turan 2026; Hamel-De le Court et al. 2026) are not "published or accepted". Not removed, per your hard rule. The unpublished project report is mentioned in the text only, not in the list. |
| C3 | Alphabetical by first author, by the stated rules (Reference list) | PASS | Sorted by `sn-basic.bst`. Şahin is encoded as `{\c{S}}ahin` so it sorts under S. |
| C4 | DOIs as full links where available | PASS | 44 entries print `https://doi.org/...`. The 11 without a DOI are listed in `05_open_questions.md`. |
| C5 | Journal names abbreviated per the ISSN LTWA, otherwise in full | PASS | Abbreviated only where certain (for example, IEEE Trans Inf Forensics Secur, Commun ACM, Future Gener Comput Syst, Sci Rep). Others are given in full. |
| C6 | Data citations carry the DataCite minimum (Data citation) | PENDING | `opol2026data` has creator, title, repository, year and DOI, but the repository and DOI are placeholders. |

## D. Tables

| # | Requirement | Status | Evidence / note |
|---|---|---|---|
| D1 | Arabic numerals | PASS | Tables 1–15 in the article; Tables S1–S4 in Online Resource 1 |
| D2 | Cited in the text in consecutive order | PASS | Script check: first citations run 1, 2, … 15. Three fixes were needed. Table I was never cited; Table VI was cited before Table V; the reasons and reconciliation tables were out of order. Table 15 was also cited in the Methods before Tables 8–14. |
| D3 | Caption explaining the table's components | PASS | All 15 captions rewritten to describe the columns. Wording only; no content changes. |
| D4 | Previously published material credited in the caption | N/A | No table reproduces published material. |
| D5 | Table footnotes as superscript lower-case letters beneath the body | PASS | Table 12, footnote "a" |

## E. Artwork

| # | Requirement | Status | Evidence / note |
|---|---|---|---|
| E1 | Vector graphics preferably EPS; named Fig1.eps and so on | PASS | Fig1.eps, Fig2.eps, Fig3.eps (EPSF-3.0) |
| E2 | Fonts embedded | PASS | Arial (ArialMT, Arial-BoldMT) embedded as Type 42; no external font resources |
| E3 | Lines at least 0.1 mm (0.3 pt) | PASS | 0.6 pt throughout; the Fig. 3 bottom box uses 1.2 pt |
| E4 | Helvetica or Arial, 8–12 pt, consistent size; no effects | PASS | 8 pt Arial throughout, with bold for the PRISMA stage labels and the Fig. 3 conclusion box. Drawn at final size (Fig. 1 is 131 mm wide = the text width) and included unscaled. |
| E5 | No titles or captions inside the artwork | PASS | None |
| E6 | Arabic numbering, cited in order; appendix figures continue the numbering | PASS | Fig. 1 → 2 → 3. There are no appendix figures. |
| E7 | Captions in the manuscript text; "Fig." and the number in bold; no punctuation after the number or at the end | PASS | `\fnum@figure` in the class prints **Fig. 1**. Captions end without a full stop. |
| E8 | Every element of the figure identified in the caption | PASS | Captions describe every box and bar. The Fig. 3 citations moved from the artwork into the caption. |
| E9 | Indicate the graphics program used | PASS | matplotlib 3.11.2 (Python), stated in the cover letter |
| E10 | Accessibility: descriptive captions; patterns or labels rather than colour alone; lettering contrast at least 4.5:1 | PASS | Greyscale only. Every bar is value-labelled and the Fig. 3 box is hatched. Black on #e6e6e6 ≈ 16.8:1; black on white 21:1. |
| E11 | No generative-AI images | PASS | All figures are drawn from data by script (`_build/make_figures.py`). |

## F. Supplementary Information and data

| # | Requirement | Status | Evidence / note |
|---|---|---|---|
| F1 | Standard formats: PDF for text and tables; .csv or .xlsx for spreadsheets | PASS | ESM_1.pdf; ESM_2.xlsx (7 audit sheets plus a README sheet) |
| F2 | Each file carries the article title, journal, author, and the corresponding author's affiliation and e-mail | PENDING | Present in both files; the city is a placeholder |
| F3 | Cited in the text as "Online Resource N" | PASS | Online Resource 1 first in the Introduction, Online Resource 2 first in Sect. 2.9 |
| F4 | Files named consecutively (ESM_1, ESM_2, …) | PASS | |
| F5 | Concise caption for each file | PASS | Back-matter "Supplementary information" section |
| F6 | Data Availability statement (Research Data Policy) | PENDING | Written. The repository name, link and DOI are placeholders. |

## G. Ethics, competing interests, declarations

| # | Requirement | Status | Evidence / note |
|---|---|---|---|
| G1 | Transparency about re-use of material (text recycling) | PENDING | "Prior dissemination and re-use of material" statement in the declarations and in the cover letter; you confirm the report's status |
| G2 | Competing-interest disclosure required for review articles | PENDING | Draft statement plus a suggested non-financial-interest disclosure |
| G3 | Funding in the declarations and in the interface | PENDING | Placeholder |
| G4 | Ethics approval and consent | PASS | "Not applicable", with the reason (published studies only; no participants, personal data or animals) |
| G5 | Data, material and code availability; author contributions | PASS / PENDING | Written; the repository is a placeholder |
| G6 | Suggested reviewers must be independent and have institutional e-mails | PENDING | Optional. Placeholders only in the cover letter, because I won't invent e-mail addresses. |

## H. Build checks

| # | Check | Status | Note |
|---|---|---|---|
| H1 | Compiles with no errors, undefined references or citations, or missing files | PASS (Tectonic) | Tectonic 0.17.0 (XeTeX + BibTeX): 0 errors, 0 undefined references, 0 undefined citations, 56 bibliography items. One 0.73 pt overfull line (Fig. 1 caption) is cosmetic. |
| H2 | pdflatex + bibtex | NOT RUN | Per your choice (Tectonic only). The source is pdflatex-ready (`pdflatex` class option, ASCII-only `.tex`). Editorial Manager compiles with pdflatex on upload, so check its generated PDF. EPS files are included, plus PDF twins so the compile cannot fail on EPS conversion. |
| H3 | Every table and figure cited, in order | PASS | `_build/check_order.py` |
| H4 | No number, table value, count or rating changed | PASS | `_build/check_numbers.py`. Every difference is new caption or Methods wording, or a number that moved into the Fig. 1 artwork. Details in `09_verification_report.md`. |

## Not specified by the guidelines (no rule invented)

- Length limit (words or pages): **not specified**.
- Article-type structure for review articles: **not specified**. The existing IMRaD-style structure was kept.
- Maximum number of references, tables or figures: **not specified**.
- Peer-review model (single- or double-anonymous): **not specified** on the page. The title page asks for author details, so the manuscript is not anonymised.
- Double line spacing: **not required by the journal**. The template manual *requests* the `[referee]` option for peer review, so it is an optional one-word change. Not applied; your call.
- Line numbers: not required; not applied.

## Conflicts between the brief, the template and the guidelines

1. **Acknowledgements location.** The template puts them in the back matter (`\bmhead{Acknowledgements}` after `\backmatter`), but the guidelines say "title page". I followed the guidelines.
2. **Declarations heading.** The guidelines use three names: "Statements and Declarations" (Title Page), "Compliance with Ethical Standards" (a separate section) and "Declarations" (Summary of requirements). I used **Statements and Declarations** and put every listed item in it, including the ethics and consent items that "Compliance with Ethical Standards" covers. Rename it if the editorial office asks.
3. **Funding.** The guidelines say funding entered in the interface "is not added to the manuscript itself", and also that it should go in the Declarations. It's in both places.
4. **"Published or accepted" references and "do not remove references".** Three arXiv preprints conflict with the reference-list rule. Your hard rule says not to remove references, so they stay, flagged.
5. **"Do not add references" and the data citation.** Adding the dataset reference was your own instruction (Step 5), and it's the only addition.
6. **The guidelines file was missing.** I used the live page; you chose this option.
