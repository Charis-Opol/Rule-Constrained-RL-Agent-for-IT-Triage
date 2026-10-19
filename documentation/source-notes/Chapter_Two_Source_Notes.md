# Chapter Two: Source and Claim Verification Notes

Working notes for `Chapter_Two.tex`. Not for submission.

## 1. What kind of review this is

- **Thematic review, not a completed systematic review.** The chapter synthesises 46 sources under five themes, one per research question. It says so in Section 2.1.
- **Your database exports were keyword-scanned, not screened.** The five exports hold 10,694 records (10,541 distinct titles): Scopus 8,663, IEEE Xplore 1,000, ACM 744, SpringerLink 284, SIAM 3. I filtered titles and abstracts by keyword. 77 records mention IT-operations terms and 19 mention incident management, incident response or AIOps specifically. I read those abstracts and kept eight studies.
- **What a proper SLR still needs:** documented search dates and strings per database, de-duplication, inclusion and exclusion criteria, title/abstract screening of all records by you, full-text screening, and a PRISMA flow diagram. The IEEE export stops at exactly 1,000 records, which looks like an export cap. The SpringerLink export has no abstracts, so the keyword scan saw only its titles.
- **Chapter One was changed in one place** to match: "a systematic review in Chapter Two will examine the gap" now reads "the literature review in Chapter Two examines the gap" (`.tex`, `.md`, `.docx`).

## 2. Depth of reading

| Group | Sources | How they were read |
|---|---|---|
| Core set in your workspace (34) | AIOps, shielding, constrained RL, deferral, agent guardrails | Text extracted from the PDFs. I read abstracts, introductions and keyword-located passages, not every paper cover to cover. |
| Not in the workspace (4) | Sutton and Barto [textbook], Kaelbling et al., Janisch et al., Joshi et al. | Cited from general knowledge of the works. Joshi et al. is described as the "Learning to Defer: A Survey" PDF describes it. |
| From your search exports (8) | Alauthman et al., Hammar and Li, Hammar et al. (NOMS), Hammar et al. (TIFS), Kim and Dán, D'Antonio and Xie, Wang et al., Ding et al. | **Abstract only**, as held in the Scopus and IEEE exports. Marked with a dagger in Table 2.1. |

**Obtain and read the full text of the eight abstract-only studies before submission.** Two of them carry the most weight in the gap argument:

- **Alauthman et al. (2026)** pairs a DQN agent with a safety shield for incident response in SCADA systems. It is the closest precedent for your design. The abstract says it provides "an evaluation plan and indicative findings"; check what was actually evaluated.
- **Hammar, Alpcan and Lupu (2026)** checks LLM-generated response actions against system constraints and abstains to collect feedback when consistency is low. Check whether a human is ever the source of that feedback.

## 3. Reference verification

- **Confirmed against Crossref:** all DOIs carried over from Chapter One, plus the six newly cited records from the IEEE and Scopus exports that I looked up.
- **Confirmed against the arXiv listing:** all arXiv identifiers, including the thirteen added in this chapter and Wu and Gong (arXiv:2604.12177).
- **Taken from the export metadata without a separate lookup:** Wang et al. (KDD 2023) and Ding et al. (ESEC/FSE 2023).
- **No stable identifier found:** Strong et al., "Learning to Defer: A Survey" (preprint dated 6 December 2025 on the PDF). It is cited without a URL.
- **Preprints with a published version you may prefer to cite:**
  - Jansen et al. (arXiv:1807.06096)
  - Yang et al. (arXiv:2303.03226)
  - Hamel-De le Court et al. (arXiv:2503.07671)
  - Wen et al. (arXiv:1503.01793)
  - Xiang et al. (GuardAgent; your file name says ICML 2025)
  - Mohammadi et al. (arXiv lists DOI 10.1145/3711896.3736570)
- Each chapter currently carries its own numbered reference list so that it compiles alone. When the chapters are merged, move the entries into one `.bib` file.

## 4. Claims that are my inference

- **Section 2.2:** the three sources of ambiguity (missing, unreliable, and multiply-consistent observations) are my grouping of what Chen et al., Remil et al., and Wu and Gong report.
- **Sections 2.3 and 2.8:** "information-gathering studies offer two options and deferral studies offer two different options" is my synthesis.
- **Section 2.4:** the statement that the use of shielding on IT-operations rule sets "remains largely unexamined" rests on this review set and the keyword scan.
- **Section 2.5:** the three baseline patterns are my grouping of the comparisons the studies report.
- **Table 2.1:** every cell is my judgement. "Not addressed or not reported" for an abstract-only study means the abstract does not mention it.
- **Section 2.8:** all five gap statements are bounded to "the reviewed literature".

## 5. Outstanding decisions

1. **Novelty is narrower than Chapter One implies.** Shielded RL for incident response has been proposed (Alauthman et al.). Chapter Two positions your contribution as the three-way triage decision, the IT service incident setting, and the joint evaluation across ambiguity levels. Chapter One has since been revised to cite Alauthman et al. and to state the gap in the same five parts.
2. **Section headings.** I organised the chapter by research question as you asked. If your department expects standard headings (theoretical review, empirical review, conceptual review), the content can be regrouped.
3. **No theoretical framework section.** The MDP and POMDP formulation is covered inside Section 2.2. Say if a separate section is required.
4. **The Directorate is not mentioned** in Chapter Two, because the chapter reviews published literature only.
5. **Not compiled.** No LaTeX distribution is installed on this machine. `Chapter_Two.tex` adds the `amssymb`, `booktabs`, `tabularx` and `caption` packages for Table 2.1, whose column headings are rotated; check that the table fits the page width.
6. **No Markdown or Word copy** of Chapter Two was produced.
