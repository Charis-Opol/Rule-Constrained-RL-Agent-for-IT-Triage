# Open questions for the author

Everything below is either a placeholder in the manuscript (printed **[in bold brackets]**) or a decision I didn't make on your behalf. Answer by number. I'll apply the answers through `_build/edits.py`, rebuild, and update the change log.

## A. Title page and declarations

**Q1. Affiliation: city and state. ANSWERED (2026-11-04).** City **Kampala**, state/region **Mukono District** (where the university is physically located). Applied.

**Q2. ORCID. ANSWERED (2026-11-04).** **0009-0003-7417-7984** confirmed correct.

**Q3. Funding. ANSWERED (2026-11-04).** (a) "No funding was received for conducting this study." Applied.

**Q4. Competing interests. ANSWERED (2026-11-04).** No competing interests. The draft's first sentence is kept; the second sentence (tying the review to the author's own undergraduate project) is **removed** at the author's request. Statement now reads: "The author has no relevant financial or non-financial interests to disclose." Applied.

**Q5. Acknowledgements. ANSWERED (2026-11-04; revised 2026-11-12).** Thanks Dr Innocent Ndibatya (guidance) and the colleagues who peer-reviewed the work. Solomon Sekamatte removed at the author's request (2026-11-12). Wrapped in `\samepage` so the section can't split across a page break.

**Q6. AI-use details (Methods Sect. 2.11). ANSWERED (2026-11-12).** Model: "Claude Opus 5.5 (Anthropic)"; no period of use stated (author's choice). The second `\tbc{}` (confirming the assistant reformatted the manuscript, condensed the abstract and drafted the statements and declarations) was removed at the author's request, not confirmed.

**Q7. Report status (re-use statement). ANSWERED (2026-11-04; applied to the manuscript 2026-11-12).** The project report is not submitted anywhere else. The "Prior dissemination and re-use of material" statement's `\tbc{}` placeholder is now resolved to a plain confirmed sentence.

## B. Data repository

**Q8. Repository and DOI. RESOLVED (2026-11-12): dropped.** The placeholder `opol2026data` Zenodo citation (with its fake `10.5281/zenodo.XXXXXXX` DOI) is removed from `references.bib` and from both the Data availability and Materials and code availability statements, per the author. Those statements now point only to Online Resource 2 (already true and already deposited with the submission), with no external-repository claim. If the audit files are deposited externally later (e.g. Zenodo) with a real DOI, re-add the citation and the repository name then.

## C. Keywords

**Q9. Confirm six keywords.** These are provisional in the manuscript:

1. Reinforcement learning
2. IT incident management
3. Incident triage
4. Escalation
5. Safe reinforcement learning
6. Systematic literature review

Swap-ins from your original Index Terms, if you'd rather: *Partially observable Markov decision process* (for 4 or 6), *Human-in-the-loop* or *Learning to defer* (for 4), *AIOps* (for 2), *Security operations* (if you want the security half of the evidence indexed).

## D. Structure

**Q10. Keep Table 1 (abbreviations)?** The guidelines don't ask for one; they only require definitions at first mention, and those are now all in the text.
- Arguments for keeping it: readers can look terms up.
- Arguments against: it duplicates the text, and it lists five abbreviations the paper never uses (CMDP, ICS, LLM, MTTR, RCA).

**My recommendation: remove it**, or failing that, delete those five rows. It's kept for now, with five rows added for terms the text now defines (IDS, IoT, IT, OT, ROC-AUC). If you remove it, every later table moves down one number. That is automatic, except "Table 9" inside Fig. 1, which the figure script regenerates.

**Q11. Framing.** See `11_framing_proposals.md` (F1–F9) and approve items by number.

**Q12. Clarifying notes (optional; data unchanged).** See `09_verification_report.md` §4–5.
- (a) Add the Dunsin et al. note explaining 20 vs 19?
- (b) Change "about a third" to "under half" in the Table 15 SRQ5 row? The count is 15/34.

**Q13. Double spacing.** The template manual asks for the `[referee]` option during peer review; the journal doesn't require it. Add it?

## E. References with missing or incomplete fields

Nothing was added or invented. Each item below needs your answer, or a confirmation that it can stay as it is.

| Ref (old number) | Key | Issue | Proposed (needs your OK) |
|---|---|---|---|
| [15] Alshiekh et al. 2018 | alshiekh2018 | You flagged the DOI as malformed-looking. **It's valid**: `10.1609/aaai.v32i1.11797` resolves to ojs.aaai.org (checked). The IEEE PDF only broke it across lines. | none |
| [46] Babar et al. 2026 | babar2026 | You flagged the DOI as malformed-looking. **It's valid**: `10.1145/3765622` resolves to dl.acm.org (checked). | none |
| [33] Kovtun et al. 2026 | kovtun2026 | No DOI. CEUR Workshop Proceedings don't issue DOIs. | Add the volume URL `https://ceur-ws.org/Vol-4242/`? |
| [6] Madras et al. 2018 | madras2018 | No DOI (NeurIPS doesn't issue them) and no pages | Supply pages if you have them, or leave as is |
| [10] Joshi et al. 2023 | joshi2023 | TMLR: no DOI or volume; OpenReview URL given | Leave as is (TMLR's standard form) |
| [19] Page et al. 2021 | page2021 | No DOI in your source | `10.1136/bmj.n71`: resolves to bmj.com (checked). Add? |
| [20] Kitchenham and Charters 2007 | kitchenham2007 | Institution is given only as "EBSE"; no URL | The usual citation is "Keele University and Durham University Joint Report, EBSE 2007-001". Confirm against your copy. |
| [52] Tong et al. 2020 | tong2020 | No DOI | `10.1609/aaai.v34i01.5442` (Crossref match on title, AAAI 34, pp. 946–953). Add? |
| [2] Remil et al. 2024 | remil2024 | arXiv preprint. The guidelines allow only published or accepted works. | Is there a published version? Otherwise keep it, and accept that the editor may query it. |
| [7] Turan 2026 | turan2026 | arXiv preprint (single author; text corrected from "et al.") | as above |
| [18] Hamel-De le Court et al. 2026 | hamel2026 | arXiv preprint | as above |
| [16] Levy et al. 2026 | levy2026 | ICLR 2026, but linked to arXiv; author list is "et al." | Supply the OpenReview link and the full author list? |
| [1] Chen et al. 2020; [14] Wang et al. 2023; [22] Ding et al. 2023 | chen2020, wang2023hrlhf, ding2023 | Author list abbreviated to "et al." in your source | Full lists are preferred but not required. Supply them? |
| [25], [26], [38], [40], [42], [48] | bompally2026, reddyavula2026, ravi2025, noorulhassan2026, bhosale2026, jaber2025 | Page numbers missing (IEEE conference papers) | Supply from IEEE Xplore, or leave as is (the DOI identifies them) |
| [54] Khozam et al. 2025 | khozam2025 | The conference is given only as "ACM International Conference Proceeding Series" | Name of the conference? |
| ~~new~~ | ~~opol2026data~~ | Dataset placeholder | **Removed** (2026-11-12, see Q8) |

## F. Cover letter

**Q14. Suggested reviewers (optional).** The journal needs **institutional** e-mails and reviewers who are fully independent of you. I haven't proposed anyone, to avoid inventing contact details. Candidates are often authors of strongly rated included studies, from different countries. If you want suggestions, name the people and I'll format them, or I can look up their current institutional pages for you to verify.

**Q15. Editor name.** Should the letter address a specific Editor-in-Chief? Check the journal's editorial board page, or keep "Dear Editor".
