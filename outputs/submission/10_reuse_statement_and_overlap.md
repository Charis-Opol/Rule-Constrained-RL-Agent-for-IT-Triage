# Re-use of material: statements and overlap report

The guidelines require "transparency on the re-use of material to avoid the concerns about text-recycling", and the journal may screen for plagiarism. The related work is your unpublished project report in `research/thesis/` (*Investigate, Recommend or Escalate: A Rule-Constrained Reinforcement Learning Agent for IT Incident Triage under Ambiguous Evidence*, BSc Computer Science, Uganda Christian University). It was in the repository, so I didn't need to ask you for it.

Under the reference-list rule, unpublished works are "mentioned in the text only". The report is therefore named in the statement but **not** added to the reference list.

## 1. Statement in the manuscript (already in *Statements and Declarations*, one [TBC])

> **Prior dissemination and re-use of material.** This review was prepared during the author's undergraduate research project at Uganda Christian University. Parts of the Introduction (the description of incident management and triage, the framing of triage as a sequence of decisions, and the requirements for rule enforcement and escalation) and the gap statements in Table 2 draw on, and in places repeat wording from, Chapters One and Two of the author's project report, *Investigate, Recommend or Escalate: A Rule-Constrained Reinforcement Learning Agent for IT Incident Triage under Ambiguous Evidence* (Uganda Christian University, 2026), which also summarises some findings of this review. [To confirm: the report is an unpublished university assessment document and has not been published or submitted to any journal.]

If the report has been deposited in a university repository, or will be by the time of publication, change the last sentence to say so and give the repository. A deposited thesis is still usually treated as unpublished for journal purposes, but say it plainly.

## 2. Statement for the cover letter

> Parts of the Introduction and the gap statements in Table 2 draw on, and in places repeat wording from, my unpublished undergraduate project report (Uganda Christian University, 2026), which this review was prepared to inform; the report in turn summarises some of this review's findings. The overlap is declared in the manuscript under "Prior dissemination and re-use of material". The report has not been published or submitted to a journal, and no part of this review has been published elsewhere.

## 3. Where the overlap is

Method: each sentence of the review was compared with Chapters One to Three of the report using shared 6-word sequences (`_build/check_overlap.py`: `python -I _build/check_overlap.py <review section .tex> <report chapter .tex ...>`). The percentage is the share of the review sentence's 6-word sequences that also appear in the chapter. Only sentences at 30% or more are listed.

### Introduction (review Sect. 1) vs report Chapter One (Introduction)

| Overlap | Review sentence (start) |
|---|---|
| 95% | "Organisations depend on IT services that are expected to remain available, and incident management is the process that restores those services…" |
| 79% | "Chen et al. describe it as the process of detecting a service problem, creating an incident, determining its cause, restoring the service…" |
| 100% | "Triage is the stage at which a reported incident is assessed and directed towards resolution." |
| 35% | "Chen et al. define it as engaging the team responsible…, and Remil et al. use the term more broadly…" |
| 70% | "Remil et al. note that data in real IT environments is commonly noisy and incomplete." |
| 100% | "A model of this kind returns an answer for every report." |
| 42% | "In RL, an agent learns a policy, which is a rule for choosing actions…" |
| 35% | "A reward signal alone does not ensure this, because penalising an undesirable action…" |
| 47% | "Studies of information gathering let an agent choose between looking further and deciding…" |

### Introduction (review Sect. 1) vs report Chapter Two (Literature review)

| Overlap | Review sentence (start) |
|---|---|
| 44% | "In their study of incident management at Microsoft, Chen et al. found that distinct problems can produce similar symptoms…" |
| 31% | "Studies of information gathering let an agent choose between looking further and deciding…" |

**Table 2, gap column:** paraphrases the five gaps in the report's Chapter Two gap summary (the paragraphs beginning "The review identifies five related gaps…"). Measured overlap is under 30% (the same ideas in different wording), but the statement declares it anyway.

### Results (review Sect. 3) vs report Chapter Two

The direction here is reversed: the report quotes or paraphrases this review's findings, which it cites as an unpublished manuscript.

| Overlap | Review sentence (start) |
|---|---|
| 68% | "How much this reflects the strength of the learned policies and how much the weakness of the baselines cannot be separated from the reports." |
| 61% | "Sahin and Mert report that an earlier version of their simulator leaked the label into the confidence signal…" |
| 41% | "Sahin and Mert show that when the scoring model degrades under dataset shift, the share of alerts deferred to analysts rises…" |
| 35% | "Kovtun et al. track a belief over a hidden attack regime in a SOC, and Koupaei and Demirkol use a Dempster-Shafer belief…" |
| 30% | "Only … studies report results over several runs with a measure of variance…" |

### Methods, Discussion, Limitations, Future research, Conclusion

There's no sentence at 30% or more. Chapter Three of the report has none either.

## 4. Optional, to reduce the overlap score

A plagiarism checker only sees the report if it has been indexed, for example in a university repository. If you want to lower the risk anyway, the four sentences at 79–100% in the first two paragraphs of the Introduction are the ones to reword. Rewording is a content decision, so I haven't touched them.
