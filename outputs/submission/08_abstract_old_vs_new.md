# Abstract: old vs new

Old: 357 words (counted from the PDF text), and it used PRISMA and IT without definitions in the abstract itself. New: **246 words** (`wc -w`), no citations, and the only abbreviations, IT and PRISMA, are defined in full. Every number is kept exactly; the table at the end tracks each one.

| Topic | Old (as printed in the IEEE PDF) | New (submission) |
|---|---|---|
| Problem | IT support teams must decide what to do with an incident before they know its cause: investigate further, apply a fix, or pass the incident to someone better placed to resolve it. | Information technology (IT) support teams must decide how to handle an incident before its cause is known: investigate further, apply a fix, or pass the incident to a person. |
| Gap in the literature | Reinforcement learning (RL) can treat this as a sequence of decisions, but the published work is spread across IT operations, security operations and safe RL. | *(dropped to meet the limit)* |
| Aim | This review asks how RL and related sequential methods have been applied to IT incident handling, which of the three decisions their agents make, how operational rules are enforced, and how the agents are evaluated. | This review examines how reinforcement learning and related sequential methods are applied to IT incident handling, which of these three decisions their agents make, how operational rules are enforced, and how the agents are evaluated. |
| Method | The review follows the PRISMA 2020 guideline. Searches of Scopus, IEEE Xplore and the ACM Digital Library on 23 October 2026 returned 4399 records. | Following the Preferred Reporting Items for Systematic Reviews and Meta-Analyses (PRISMA) 2020 guideline, searches of Scopus, IEEE Xplore and the ACM Digital Library on 23 October 2026 returned 4,399 records. |
| Selection | After the removal of 73 duplicates and 4195 records by automated filtering, 131 records were screened on title and abstract, 47 reports were sought, 40 were assessed in full, and 34 studies published between 2020 and 2026 were included. | After 73 duplicates were removed and 4,195 records were filtered out automatically, 131 were screened, 40 reports were assessed in full, and 34 studies (2020–2026) were included |
| Appraisal | Their quality was appraised with an eight-item checklist, and the evidence was synthesised narratively around five review questions. | and appraised with an eight-item checklist. |
| Finding 1 | There are four main findings. First, only 4 studies represent the hidden state of an incident with an explicit belief, and most treat it as fully observed. | Four studies represent the hidden incident state with an explicit belief. |
| Finding 2 | Second, 17 studies give the agent an explicit information-gathering action, but only 7 include escalation to a person, and only one combines gathering, a response action and escalation, with the escalation fixed by design rather than learned. | Seventeen give the agent an information-gathering action and 7 include escalation to a person; only one combines all three decisions, and its escalation is fixed by design rather than learned. |
| Finding 3 | Third, rule enforcement is proposed more often than it is measured: 5 studies use a hard filter or shield, and 3 report what happens to a blocked or uncertain decision. | Five use a hard filter or shield, and 3 report what happens to a blocked or uncertain decision. |
| Finding 4 | Fourth, decision quality is measured in 31 studies but escalation behaviour in 5 and constraint compliance in 4, and robustness to changing conditions is tested in 15. | Decision quality is measured in 31 studies, escalation behaviour in 5, constraint compliance in 4, and robustness in 15. |
| Evidence base | The evidence is recent, with 27 studies published in 2025 or 2026, and uneven in quality: 12 studies meet at most two of the eight checklist items. | The evidence is recent (27 studies from 2025 or 2026) and of uneven quality: 12 meet at most two checklist items. |
| Conclusion | The review concludes that a single policy which learns to investigate, act or escalate for IT service incidents under explicit rules has not been reported, and it sets out the evaluation that such work should include. | No study reports a single policy that learns to investigate, act or escalate for IT service incidents under explicit rules. |

## Numbers check

| Number | Old | New |
|---|---|---|
| Search date 23 October 2026 | ✓ | ✓ |
| Records identified 4399 | ✓ | ✓ (printed 4,399) |
| Duplicates 73 | ✓ | ✓ |
| Removed by automation 4195 | ✓ | ✓ (printed 4,195) |
| Screened 131 | ✓ | ✓ |
| Reports sought 47 | ✓ | **omitted** |
| Assessed 40 | ✓ | ✓ |
| Included 34; years 2020–2026 | ✓ | ✓ |
| Eight-item checklist | ✓ | ✓ |
| Belief 4; information gathering 17; escalation 7; all three 1 | ✓ | ✓ |
| Hard filter 5; blocked handling 3 | ✓ | ✓ |
| Decision quality 31; escalation 5; compliance 4; robustness 15 | ✓ | ✓ |
| Recent 27; low quality 12 (at most two of eight items) | ✓ | ✓ |

**Dropped to meet the 250-word limit, with no change to any value:** "47 reports were sought"; "most treat it as fully observed"; the sentence on the work being spread across IT operations, security operations and safe RL; "synthesised narratively around five review questions"; "rule enforcement is proposed more often than it is measured"; and "it sets out the evaluation that such work should include". If you want one back, the main thing to trim instead is the full PRISMA name (11 words). The guideline requires abbreviations to be defined, so it can only go if PRISMA is dropped from the abstract altogether.

Thousands separators (4,399 and 4,195) are typographic only. Remove them if you'd rather match the body text, which prints 4399.
