# Chapter One: Source and Claim Verification Notes

Working notes for `Chapter_One.tex` (with `Chapter_One.md` and `Chapter_One.docx` kept in step). Not for submission.

## 1. What was inspected

| Location | Contents | How it was used |
|---|---|---|
| `Papers for the introduction/OPOL CHARIS Research Chapter One.pdf` | Your earlier Chapter One (LSTM-FNN credit-risk study) | Read in full. The only writing sample; source of style and formatting conventions. |
| `Papers for the introduction/` (17 research papers) | AIOps, safe RL, shielding, learning to defer, NIST AI RMF | Text extracted; title, abstract, introduction and keyword-located passages read. Not read cover to cover. |
| `Papers/` (20 papers) | Shielding, constrained RL, LLM agent guardrails, escalation | Opening text read for seven; three cited ([10], [22], [23]). The rest were not needed for Chapter One. |
| `Raw imports of the searches the SLR/` | Database exports (Scopus, IEEE Xplore, ACM, Springer, SIAM) for a safe-RL search string | Inspected only. They are unscreened search results, so nothing was cited from them. |

**Not found in the workspace:** university or departmental formatting guidelines, a project proposal, an SLR protocol, supervisor feedback, a literature review, or any project code. The chapter therefore relies on your brief for project-specific facts (aim, objectives, incident categories, simulation-only evaluation).

## 2. Conventions taken from your sample

- Title block (title, name, registration numbers), then `CHAPTER ONE` and `1. INTRODUCTION`.
- Numbered sections; objectives split into General Objective and Specific Objectives; "This study will answer/test the following…" lead-ins; hypotheses labelled H1–H3.
- IEEE numeric citations in order of first appearance, placed before the full stop; references with "[Online]. Available:" links.
- British spelling; justified paragraphs with space between them and no first-line indent.
- Paragraphs of five to eight sentences that open with a claim, attribute findings to named authors ("Chen et al. found…"), and close on a consequence ("therefore…").

The sample is typeset in LaTeX, and `Chapter_One.tex` follows it: 12 pt article class, unnumbered `CHAPTER ONE` and `1. INTRODUCTION` headings, sections numbered 1.1 onwards, numeric citations, blue URLs in the reference list. The preamble values (1-inch margins, one-and-a-half spacing) are estimated from the sample PDF because its source file is not in the workspace. The file has not been compiled: no LaTeX distribution is installed on this machine. The Word file is a secondary copy in Times New Roman 12 pt.

## 3. Claims and supporting sources

Checked = I located the supporting passage in the PDF in your workspace.

| Claim in the chapter | Source | Status |
|---|---|---|
| An incident is an unplanned interruption or outage of a service; incident management covers detection, incident creation, cause, restoration, knowledge capture | [1] abstract, §2.2.1 | Checked |
| Slow handling reduces availability, causes financial loss and user dissatisfaction | [1] §1; [2] §1.1 | Checked. The dollar figures in both papers were deliberately left out. |
| Triage = engaging the responsible team | [1] §2.2.1 | Checked |
| Triage more broadly covers prioritisation, assignment, classification, duplicates | [2] incident-management procedure section | Checked |
| Rule-based and expert systems are limited in adaptiveness, efficiency, scalability | [2] §1.1 | Checked |
| AIOps models classify, prioritise and assign incidents | [1] (auto-triage model), [2] | Checked |
| LLMs extend AIOps to root cause analysis and mitigation suggestions | [3] §4 | Checked |
| Automation mainly stops at triage or solution recommendation; automatic execution is limited and unverified | [3] §1 and §4.3 | Checked; wording kept close to the source |
| Distinct problems produce similar symptoms; incidents are reassigned several times | [1] §1 | Checked |
| Delays come from incomplete dependencies and imprecise health assessment | [1] abstract, §4 | Checked |
| Real IT data is commonly noisy and incomplete; robustness is a requirement | [2] requirements section | Checked |
| Triage approaches are evaluated with classification/ranking metrics | [2] metrics section | Checked. "Many triage models treat the task as a single prediction" is my inference from this, not a quoted finding. |
| RL: an agent learns a policy from reward through interaction | [4] | Standard textbook; not in workspace, not re-read |
| Under partial observability, actions can gather information at a cost | [5] | Metadata verified; content from my knowledge of the paper, not re-read |
| RL can learn which costly features to acquire before deciding | [6] | Metadata verified; content from my knowledge of the paper, not re-read |
| RL applied to security incident response strategy selection | [7] abstract, §1 | Checked |
| Malware investigation modelled as an MDP | [8] abstract | Checked |
| Neither [7] nor [8] reports rule checking or hand-off to a human | [7], [8] | Based on keyword search (constraint, shield, defer, escalate, human, operator) and partial reading. **Confirm by reading both papers.** |
| RL maximises reward without guaranteeing safety | [9] abstract | Checked |
| Reward penalties do not guarantee unsafe actions are never chosen | [10] introduction | Checked |
| Safe RL definition | [11] abstract | Checked |
| Constraints on expected cumulative cost | [12], [13] | Checked |
| Many practical constraints are instantaneous, state-wise | [14] §1 | Checked |
| A shield monitors actions and corrects only violations | [9] abstract | Checked |
| Shield guarantees depend on the specification and environment model | [10] | Checked |
| "Automatic healing actions need to be executed safely" | [2] capabilities section | Checked |
| Selective prediction lets a model abstain | [15] | Checked |
| Learning to defer trains a model to decide when a human takes over | [16] | Checked |
| Learning to defer needs expert-decision data | [17] abstract | Checked |
| How deferral is communicated affects human accuracy | [18] abstract | Checked |
| Deferral extended to sequential settings | [19] | Checked only through the description in the "Learning to Defer: A Survey" PDF. **Read the paper.** |
| AI may decide, defer to an expert, or act as an additional opinion; roles must be defined | [20] Appendix C | Checked |
| An unguarded LLM agent failed to escalate policy-mandated cases | [21] abstract | Checked. Domain is employee onboarding, stated as "outside IT operations". |
| Escalation treated as a cost-aware, uncertainty-based decision | [22] abstract | Checked. Preprint. |
| Human attention is finite; over-escalation can weaken oversight | [23] abstract | Checked. Single-author preprint reporting a modelling result, so the chapter says "may". |
| Safe RL demonstrated mainly in control/robotics; learning to defer mostly single-step | [12], [14], [16], [17] | Reasonable from these sources but a generalisation. Chapter Two should test it. |

## 4. Reference verification

- **DOI and metadata confirmed against Crossref:** [1], [3], [5], [6], [7], [8], [9], [10], [13], [14], [17], [18], [20], [21].
- **Confirmed on arXiv:** [2], [22], [23]. For [19], arXiv:2109.06312 exists; the TMLR 2023 venue and OpenReview link come from the survey's reference list.
- **Page ranges confirmed on the PMLR site:** [12], [15].
- **From the PDF and general knowledge only:** [4] (not in the workspace), [11] (issue number 42 from memory), [16] (volume 31 from the conference year).
- **Check before submission:** whether [2] now has a peer-reviewed version to cite in place of the arXiv preprint.
- **In the workspace but not cited:** "Learning to Defer: A Survey" (Strong et al., preprint dated December 2025). I could not find a stable identifier for it.
- [1], [3], [18] and [22] are shortened to "et al." following IEEE practice for seven or more authors.

## 5. Your own claims versus the literature

- The research gap is worded as "the studies reviewed for this chapter do not examine…". It is a claim about the papers read here, not about the whole field. The problem statement says so and defers the fuller test to Chapter Two.
- The database-restart rule in §1.1 is an illustration I wrote, not a cited fact.
- No experimental results, incident volumes, resolution times or performance figures appear anywhere in the chapter.
- No confidential incident data, credentials or personal data are used. No text is copied from the sample.

## 6. Outstanding decisions

1. **Chapter structure.** Your sample has five sections; your brief lists eleven. I kept the sample's conventions and added the sections you asked for. If the department expects the shorter form, sections 1.6, 1.7, 1.9, 1.10 and 1.11 can be removed without breaking the argument.
2. **Research Hypotheses (1.5).** Your brief did not list hypotheses. I added three because your sample has them. H2 assumes one baseline is the same agent without the safety mechanism, and H3 assumes ambiguity is a controllable level in the simulation. Remove or adjust if either is not planned.
3. **Conceptual Framework (1.9) and Figure 1.1.** Included without a guideline requiring it. The text says a violating proposal "is prevented from taking effect" and leaves open what replaces it (re-selection, forced escalation, or a penalty). That is a Chapter Three design decision.
4. **Baselines.** Named only as examples in 1.10 (fixed rule-based policy; agent without the safety mechanism). Confirm the final set with your supervisor.
5. **Incident categories.** The four categories are marked "provisionally", taken from your brief.
6. **Role of the UCU Directorate of University ICT Services.** You said part of the study will be carried out with the Directorate but not which part. The chapter says its practice is expected to inform the simulated scenarios and operational constraints, and that the form of involvement (consultation with technicians, anonymised incident records) will be agreed with the Directorate. Replace this with the actual arrangement once it is settled, and say whether a letter of permission or ethical clearance has been obtained.
7. **Simulated technician.** The chapter states that the technician who receives escalations is simulated and that the experiments do not put the agent's decisions before working technicians. Change this if Directorate staff will evaluate the agent.
8. **Recommend versus execute.** The scope states that the agent recommends actions and never executes them on live systems.
9. **Title block.** Name and registration numbers are copied from your sample; confirm they apply to this project, and add the supervisor, department and date if required.
10. **SLR.** The problem statement says Chapter Two contains a systematic review. The search exports suggest one is under way, but no protocol is in the workspace.

## 7. Revision after the literature review (Chapter Two)

Chapter One was revised so that its background, problem statement and gap match Chapter Two. Reference numbers changed: the list now has 28 entries, and the numbers in the table in section 3 above refer to the earlier 23-entry list.

- **Five sources added**, all found in your search exports and **read at abstract level only**: Wang et al. (KDD 2023), Kim and Dan (2025), Hammar and Li (2025), Alauthman et al. (2026), and Hammar, Alpcan and Lupu (2026). Read the full texts before submission.
- **Background:** the paragraph on reinforcement learning now covers sequential methods in IT operations and security incident handling, and the paragraph on constraints now reports the shielded agent proposed by Alauthman et al. and the constraint check of Hammar et al.
- **Gap wording:** the background now says the strands "meet in pairs" (gather-or-decide, decide-or-defer, policy-plus-shield). The problem statement lists the five gaps from Chapter Two and states that constraining a learned incident-handling agent is not claimed as new.
- **Unchanged:** aim, objectives, research questions, hypotheses, scope, significance, conceptual framework and definitions.
- The pre-revision text is not kept in the project folder.
