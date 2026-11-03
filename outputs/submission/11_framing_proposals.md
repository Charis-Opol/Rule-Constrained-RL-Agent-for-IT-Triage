# Standalone framing: proposals (nothing applied yet)

A journal reader doesn't know "the project", "Chapter Two", "the thematic review" or "the planned agent". The submission currently keeps the original wording everywhere, as you asked. Below are proposals. Approve them by number (for example "F1, F2a, F4, F6–F9") and I'll apply them through `_build/edits.py`, rebuild, and log them in the change log.

**Recommended overall approach:** keep **one** clear disclosure that the review was motivated by the author's own planned study, because that is honest and is the bias statement the Limitations rely on. Everywhere else, refer to the design generically as *a three-way triage agent* or *an agent that investigates, recommends or escalates*. Section 4.7 becomes "Implications for research". This removes every unexplained reference without hiding the motivation.

## F1: Introduction, paragraph 5 (the thematic review / Chapter Two)

**Now:** "The literature review for the project of which this review is part (Chapter Two of the project report) found that these strands have developed largely apart. … That review was thematic and not systematic. It drew on a core set of collected publications and on a database search run on 13 October 2026, which returned 10,694 records that were filtered by keyword and not screened. Its conclusions about gaps were therefore conclusions about the literature it had read. This review replaces that search…"

**Proposed:** "An earlier, non-systematic review by the author, conducted for an undergraduate research project, found that these strands have developed largely apart. … That review was thematic. It drew on a core set of collected publications and on a database search run on 13 October 2026, which returned 10,694 records that were filtered by keyword and not screened, so its conclusions about gaps were conclusions about the literature it had read. The present review replaces that search…"

(The numbers 13 October 2026 and 10,694 are kept.)

## F2: Introduction, paragraph 6 (the planned agent and bias)

**Now:** "The project plans an RL agent for IT incident triage that chooses among requesting a diagnostic check, … The agent is to be trained and evaluated in simulation. Because this review prepares for that study, it could lean towards the planned design. Three measures limit this. …"

**Proposed (F2a, keeps the disclosure):** "The author's planned study concerns an RL agent for IT incident triage that chooses among requesting a diagnostic check, recommending a fix that the organisation's operational rules permit, and escalating to a human expert, with every proposal checked by an independent rule-based mechanism, and that is trained and evaluated in simulation. We refer to this as a *three-way triage agent*. Because this review was undertaken to inform that study, it could lean towards that design. Three measures limit this. …"

**Alternative (F2b, more neutral):** the same, but starting "This review is motivated by a design of interest: an RL agent that…" and moving the sentence on the author's planned study to the declarations (Competing interests, non-financial).

## F3: Introduction, paragraph 7, and Table 2 (RQ1–RQ5 and "the project question")

**Now:** the text says Table 2 gives "the research question of the project that it informs", and Table 2 has a column "Project question informed" (RQ1–RQ5 with short glosses) and a column header "Gap that motivated it (from the thematic review)".

**Proposed (F3a, recommended): delete the "Project question informed" column.** The SRQ column already carries the question, and RQ1–RQ5 are never defined. Then change the gap header to "Gap that motivated it (from the earlier thematic review)", and the sentence to "Table 2 gives the five specific objectives (SO1–SO5), the review question each answers, and the gap that motivated it. The gaps are those stated by the earlier thematic review (Sect. 1); Sect. 4 returns to each in the light of the included evidence."

**Alternative (F3b):** keep the column, rename it "Design question informed", and define RQ1–RQ5 once in the text.

## F4: Methods (three phrases)

| Location | Now | Proposed |
|---|---|---|
| Sect. 2, para 1 | "because the earlier search for the project returned too many records to screen" | "because the earlier thematic search (Sect. 1) returned too many records to screen" |
| Sect. 2.1 | "SpringerLink and SIAM, which were searched for the project's earlier review, were dropped" | "SpringerLink and SIAM, which were searched for the earlier thematic review, were dropped" |
| Sect. 2.7 | "following the project's evaluation plan" | "chosen to match the evaluation needs of a three-way triage agent" |

## F5: Results (phrases that assume the reader knows "the project")

| Location | Now | Proposed |
|---|---|---|
| Sect. 3.1 | "which the project's thematic review had treated as the closest precedent" | "which the earlier thematic review had treated as the closest precedent" |
| 3.5.1 | "so the representation the project needs exists and has been evaluated" | "so the representation a three-way triage agent needs exists and has been evaluated" |
| 3.6.2 | "as the project does" | "as a three-way triage agent would" |
| 3.6.4 | "The three-way decision the project studies is therefore not covered" | "The three-way decision is therefore not covered" |
| 3.7 intro | "which is the distinction the project's design depends on" | "which is the distinction on which rule-constrained designs depend" |
| 3.7.3 | "which is the project's rule" | "a rule that a three-way triage agent might adopt (one re-proposal, then escalation)" |
| Table 15 interpretations (6 cells) | "the project needs", "as the project assumes", "of the project", "The project's rule", "the project plans", "the project should keep one", "the project agent" | the same substitutions: "a three-way triage agent", or simply drop the clause (for example, "A rule-based baseline is standard and should be kept") |

## F6: Discussion, opening and Sects 4.1–4.5 ("the thematic review", "the project")

- "each part of the planned design" → "each part of a three-way triage agent".
- "sets out what the findings imply for the project" → "sets out what the findings imply for research on such agents".
- "The thematic review stated/found …" (five places) → "The earlier thematic review stated/found …". This is minimal; it's defined once in F1.
- 4.2: "The closest work to the project is therefore…" → "The closest work is therefore…"; "The project's question is whether…" → "The open question is whether…".
- 4.3: "The more important finding for the project is what is missing." → "The more important finding is what is missing."; "The project's rule, that a blocked agent may make one further proposal…, has no direct precedent." → "A rule that lets a blocked agent make one further proposal before the incident is escalated has no direct precedent."
- 4.4: "the failure modes the project's evaluation is most exposed to, because it too will train and test in a simulator it builds" → "the failure modes to which any evaluation in a purpose-built simulator is exposed".
- 4.5: "That curve is what the project's fifth research question asks for." → "That curve is the missing measurement."

## F7: Section 4.7 "Implications for the Project" and Fig. 3

- Heading → **"Implications for Research on Three-Way Triage Agents"**.
- "Fig. 3 places the project against the evidence. Each of its four components…" → "Fig. 3 sets the four components of a three-way triage agent against the evidence. Each component…".
- "The findings suggest six things for the project's design and evaluation." → "The findings suggest six requirements for the design and evaluation of such agents." The six items are unchanged.
- Fig. 3 caption: "Components of the planned agent" → "Components of a three-way triage agent". The artwork needs no change.

## F8: Limitations, last paragraph

**Now:** "Finally, the review was written to prepare for a particular study, and the themes were coded against that study's design."

**Proposed:** "Finally, the review was undertaken to inform the author's planned study of a three-way triage agent (Sect. 1), and the themes were coded against that design." This keeps the bias limitation and makes the reference explicit.

## F9: Conclusion, last sentence

**Now:** "Within those limits, the review supports the project's plan to study such an agent, and it indicates what the evaluation must include: …"

**Proposed:** "Within those limits, the review supports research on such an agent and indicates what its evaluation must include: …" (the list is unchanged).

---

### Interaction with other items

- If you approve F3a, the RQ abbreviation problem disappears (checklist B3) and Table 2 gets narrower.
- If you approve F2b, extend the Competing-interests text to state the non-financial interest explicitly.
- None of these proposals changes a number, classification or conclusion. They only change who is referred to.
