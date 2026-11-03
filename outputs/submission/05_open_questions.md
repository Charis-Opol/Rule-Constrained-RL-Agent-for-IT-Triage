# Open questions for the author

Everything below is either a placeholder in the manuscript (printed **[in bold brackets]**) or a decision I didn't make on your behalf. Answer by number. I'll apply the answers through `_build/edits.py`, rebuild, and update the change log.

## A. Title page and declarations

**Q1. Affiliation: city and state.** The affiliation reads "Department of Computing and Technology, Faculty of Engineering, Design and Technology, Uganda Christian University, **[city]**, **[state or region, if used]**, Uganda". Which city? Do you want a region or district, or none? The guidelines mark state as optional.

**Q2. ORCID.** Is **0009-0003-7417-7984** correct? It came from the original `\orcid` macro, which the repo README flags "to verify".

**Q3. Funding.** Which applies?
- (a) "No funding was received for conducting this study." (wording from the guidelines)
- (b) Funding from [funder, written in full] under grant [number]. The same text must also go in the submission interface.

**Q4. Competing interests.** The current draft is: "The author has no relevant financial or non-financial interests to disclose. The review was carried out to inform the author's own undergraduate research project on a reinforcement learning agent for IT incident triage." Keep both sentences? I recommend keeping the second as a **non-financial** interest: it matches the bias statement in Sect. 1 and in the Limitations. Do you have any other interests, such as employment, consultancy or a board role?

**Q5. Acknowledgements.** Who should be acknowledged, if anyone? The report's title page names a primary advisor (shown as a red placeholder in the thesis source). If you name your supervisor, check that they agree. Or delete the section.

**Q6. AI-use details (Methods Sect. 2.11).**
- (a) Which Claude model or version, and over what period (for example, October–November 2026)?
- (b) Confirm the bracketed sentence: "the assistant was also used to reformat the manuscript for this journal, condense the abstract and draft the statements and declarations, and the author reviewed and approved these changes". It describes this preparation work, which is more than "AI-assisted copy editing" as the guidelines define it (it includes generative editorial work), so I think it should stay once you have reviewed the changes.

**Q7. Report status (re-use statement).** Confirm that the project report is unpublished and has not been submitted to a journal. Has it been, or will it be, deposited in a university repository?

## B. Data repository

**Q8. Repository and DOI.** I recommend **Zenodo**: free, DOI on deposit, and a GitHub release can be archived automatically. Alternatives are OSF and Figshare. Deposit these files:
- `research/slr/audit/`: the seven CSVs, `generate.py` and `review_data.py`.
- `research/slr/README.md`.

Don't deposit the raw database exports or the PDFs, which are already git-ignored for licence reasons. Send me the repository name and DOI, and I'll fill in the Data availability statement and the `opol2026data` reference (title, year and DOI).

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
| new | opol2026data | Dataset placeholder | Repository and DOI (Q8) |

## F. Cover letter

**Q14. Suggested reviewers (optional).** The journal needs **institutional** e-mails and reviewers who are fully independent of you. I haven't proposed anyone, to avoid inventing contact details. Candidates are often authors of strongly rated included studies, from different countries. If you want suggestions, name the people and I'll format them, or I can look up their current institutional pages for you to verify.

**Q15. Editor name.** Should the letter address a specific Editor-in-Chief? Check the journal's editorial board page, or keep "Dear Editor".
