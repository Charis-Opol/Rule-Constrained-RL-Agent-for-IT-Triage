# WBS: Rule-Constrained RL for Ambiguity-Aware IT Incident Triage

**Owner:** Opol Charis (solo project) · **Plan start:** Mon 19 Oct 2026 · **Plan end:** Sun 29 Nov 2026
**Source:** `documentation/milestone/WBS_Six_Weeks.docx`, updated after the stakeholder interview of 19 Oct 2026.
**Effort:** 38.0 working days over six weeks: the original 36.5 plus 1.5 for stakeholder work in Week 1.

## How this file maps to Trello

- **Board:** `FYP – RL Incident Triage`
- **Lists (left to right):** `Backlog` · `This Week` · `Doing` · `Waiting on others` · `Done`
- **One card per task** (the `### ` headings below). The card title is the heading text.
- **Labels:** one per work package (`WP0` … `WP9`), plus `Milestone`, `Blocked`, `Optional`.
- **Due date:** the `Due` field (end of the planned week, 18:00 EAT).
- **Description:** `Deliverable`, `Depends on`, `Days`.
- **Checklist:** the bullet list under `Checklist`. The card is done when every item is ticked.
- **Status:** `Done` → Done list · `Waiting` → Waiting on others · `Todo` → This Week if due this week, otherwise Backlog.

## Weeks at a glance

| Week | Dates | Focus | Milestone (end of week) |
|---|---|---|---|
| 1 | 19–25 Oct | Stakeholder follow-up; elicitation; start simulator | M1 Draft scenario model; simulator generates incidents |
| 2 | 26 Oct–1 Nov | Finish simulator; rule checker; first baselines | M2 Scenario model frozen after staff review; three baselines run end to end |
| 3 | 2–8 Nov | Train agent; finish baselines | M3 Trained DQN (10 seeds) with and without the rule checker |
| 4 | 9–15 Nov | Main comparison and ablations | M4 Results for Experiments 1–3 |
| 5 | 16–22 Nov | Robustness; analysis; start prototype | M5 Robustness results; replay screen working |
| 6 | 23–29 Nov | Prototype, poster, write-up | M6 Prototype, poster and Chapter 4 draft ready |

**Critical path:** 0.3 Directorate letter → 1.1 NDA → 2.2 Elicitation → 2.3 Scenario model → 3.2–3.3 Simulator → 3.7 Freeze → 6.1–6.4 Training → 7.1 Experiment 1 → 7.6 Analysis → 9.1 / 9.3 Chapter 4 and poster.
**If Week 1 input from the Directorate is late:** use 2.4 (provisional model) so 3.x can start. Replace it when their input arrives.
**Cut order if time runs short:** 7.7 (PPO, randomised training) → 7.4 (sensitivity) → seeds from 10 to 5. Never cut: simulator, DQN, rule checker, baselines, the four measures.

---

## WP0 Stakeholder engagement (after interview)

### 0.1 Write up interview findings
- **Status:** Done · **Due:** 2026-10-19 · **Days:** 0.25 · **Label:** WP0
- **Deliverable:** `documentation/stakeholder/private/Interview_01_Findings_2026-10-19.md` (not in the repo)
- **Depends on:** —
- **Checklist:**
  - [x] Findings by theme
  - [x] Implications and changes table
  - [x] Open questions list
  - [ ] Save transcript PDF into `documentation/stakeholder/private/`

### 0.2 Update chapters after interview
- **Status:** Done · **Due:** 2026-10-19 · **Days:** 0.25 · **Label:** WP0
- **Deliverable:** Revised Chapters 1–3 and Figure 1.1; updated elicitation workbook
- **Depends on:** 0.1
- **Checklist:**
  - [x] Categories now application-led (provisional)
  - [x] "Technician" → "human expert" / "IT staff"
  - [x] Consultation, ethics and limitations text
  - [x] Workbook: new categories, evidence source, remedy approval columns
  - [ ] Supervisor has seen the change of setting

### 0.3 Letter to the Director seeking collaboration
- **Status:** Todo · **Due:** 2026-10-21 · **Days:** 0.25 · **Label:** WP0
- **Deliverable:** Signed letter delivered (`documentation/stakeholder/letter/`)
- **Depends on:** —
- **Checklist:**
  - [x] Contact details, salutation and supervision filled in
  - [x] Date filled in (20 Oct 2026)
  - [x] Signed (digital signature added; department signature block removed)
  - [ ] Print and deliver, or email as PDF
  - [ ] Record date sent

### 0.4 Three-page proposal to Mr Simon
- **Status:** Todo · **Due:** 2026-10-21 · **Days:** 0.5 · **Label:** WP0
- **Deliverable:** `documentation/stakeholder/proposal/` PDF sent to Mr Simon
- **Depends on:** 0.1
- **Checklist:**
  - [ ] Fill in bracketed placeholders
  - [ ] Read through once for tone
  - [ ] Send with the elicitation workbook attached
  - [ ] Ask for a 60–90 minute elicitation session and a date

### 0.5 Follow-up: consent, categories, open questions
- **Status:** Waiting · **Due:** 2026-10-23 · **Days:** 0.25 · **Label:** WP0
- **Deliverable:** Written answers / meeting notes in `documentation/stakeholder/private/`
- **Depends on:** 0.4
- **Checklist:**
  - [ ] Consent to use interview statements
  - [ ] Categories confirmed or changed
  - [ ] Answers to the 8 open questions in the findings doc
  - [ ] If categories change, update Ch1 scope, Ch3 §3.3, workbook

---

## WP1 Project management and approvals

### 1.1 Sign NDA; confirm ethics position with supervisor
- **Status:** Waiting · **Due:** 2026-10-23 · **Days:** 0.5 · **Label:** WP1
- **Deliverable:** Signed NDA; note of ethics position
- **Depends on:** 0.3
- **Checklist:**
  - [ ] NDA signed and filed
  - [ ] Check NDA allows publishing derived scenarios and rules
  - [ ] Ethics requirement confirmed with supervisor

### 1.2 Set up repository, folders and weekly progress log
- **Status:** Todo · **Due:** 2026-10-20 · **Days:** 0.5 · **Label:** WP1
- **Deliverable:** Repository with README and `documentation/progress_log.md`
- **Depends on:** —
- **Checklist:**
  - [x] Folders organised (research/, documentation/); README and .gitignore written
  - [ ] Git repo initialised and pushed
  - [ ] Code folders: `src/sim/`, `src/agents/`, `src/rules/`, `experiments/`, `results/`
  - [ ] `.gitignore` excludes Directorate data

### 1.3 Weekly supervisor check-in and plan update
- **Status:** Todo · **Due:** 2026-11-29 · **Days:** 2.0 · **Label:** WP1
- **Deliverable:** Dated log entries; updated plan and Trello board
- **Depends on:** —
- **Checklist:**
  - [ ] Week 1 · [ ] Week 2 · [ ] Week 3 · [ ] Week 4 · [ ] Week 5 · [ ] Week 6

---

## WP2 Scenario elicitation with the Directorate

### 2.1 Prepare elicitation template
- **Status:** Done · **Due:** 2026-10-19 · **Days:** 0.5 · **Label:** WP2
- **Deliverable:** `research/elicitation/Directorate_Elicitation_Workbook.xlsx`
- **Depends on:** —
- **Checklist:**
  - [x] Causes, checks, symptoms, context, likelihood grids, rules, costs
  - [x] Updated after interview

### 2.2 Run elicitation session(s)
- **Status:** Waiting · **Due:** 2026-10-24 · **Days:** 1.0 · **Label:** WP2
- **Deliverable:** Completed workbook; session notes
- **Depends on:** 1.1, 2.1, 0.4
- **Checklist:**
  - [ ] Session booked
  - [ ] Causes and remedies (25)
  - [ ] Checks (20) and symptoms
  - [ ] Likelihood ratings
  - [ ] Rules (10) with approval levels
  - [ ] Ask for anonymised ticket counts

### 2.3 Write up scenario model v1
- **Status:** Todo · **Due:** 2026-10-25 · **Days:** 1.0 · **Label:** WP2
- **Deliverable:** Scenario model v1 (config files from the workbook)
- **Depends on:** 2.2
- **Checklist:**
  - [ ] Export workbook to YAML/JSON
  - [ ] Likelihood tables loaded and validated
  - [ ] Ten rules in readable form

### 2.4 Contingency: provisional model if input is late
- **Status:** Todo · **Due:** 2026-10-22 · **Days:** 0.0 · **Label:** WP2, Optional
- **Deliverable:** Provisional model, marked as such
- **Depends on:** 2.1
- **Checklist:**
  - [ ] Only if no Directorate input by Thu 22 Oct
  - [ ] Draft from the interview and the literature

---

## WP3 Incident simulator

### 3.1 Install and check tools
- **Status:** Todo · **Due:** 2026-10-20 · **Days:** 0.5 · **Label:** WP3
- **Deliverable:** Working environment; `requirements.txt`
- **Depends on:** 1.2
- **Checklist:**
  - [ ] Python, Gymnasium, Stable-Baselines3 installed
  - [ ] Versions pinned

### 3.2 Incident generator
- **Status:** Todo · **Due:** 2026-10-25 · **Days:** 1.0 · **Label:** WP3
- **Deliverable:** Generator module
- **Depends on:** 2.3 or 2.4
- **Checklist:**
  - [ ] Draw hidden cause and context
  - [ ] Generate symptoms and true check results
  - [ ] Seeded and reproducible

### 3.3 Gymnasium environment
- **Status:** Todo · **Due:** 2026-10-25 · **Days:** 1.5 · **Label:** WP3, Milestone
- **Deliverable:** Environment (evidence vector, 36 actions (20 checks + 15 fixes + escalate), rewards, step limit)
- **Depends on:** 3.2
- **Checklist:**
  - [ ] One-hot evidence vector (checks 4 values, symptoms 3)
  - [ ] Masks for blocked and already-requested actions
  - [ ] Rewards and step limit
  - [ ] **M1 reached**

### 3.4 Three ambiguity controls
- **Status:** Todo · **Due:** 2026-11-01 · **Days:** 1.0 · **Label:** WP3
- **Deliverable:** Configurable ambiguity levels
- **Depends on:** 3.3
- **Checklist:**
  - [ ] Missing evidence (p_miss)
  - [ ] Unreliable evidence (p_noise)
  - [ ] Overlap (ω)

### 3.5 Reference labels
- **Status:** Todo · **Due:** 2026-11-08 · **Days:** 0.5 · **Label:** WP3
- **Deliverable:** Label function (resolvable / should escalate)
- **Depends on:** 3.3

### 3.6 Simulator tests
- **Status:** Todo · **Due:** 2026-11-01 · **Days:** 1.0 · **Label:** WP3
- **Deliverable:** Test report
- **Depends on:** 3.3
- **Checklist:**
  - [ ] Unit tests
  - [ ] Random policy sanity run
  - [ ] Oracle policy (knows the cause) sanity run

### 3.7 Staff review; freeze scenario model
- **Status:** Todo · **Due:** 2026-11-01 · **Days:** 1.0 · **Label:** WP3, Milestone
- **Deliverable:** Review notes; frozen model v2
- **Depends on:** 3.6, 2.2
- **Checklist:**
  - [ ] Sample incidents sent to Directorate
  - [ ] Revisions made
  - [ ] Model frozen (tagged in git) before any training
  - [ ] **M2 reached (with 5.1, 5.3)**

---

## WP4 Rule checker

### 4.1 Encode the ten rules
- **Status:** Todo · **Due:** 2026-11-01 · **Days:** 0.5 · **Label:** WP4
- **Deliverable:** Rules file
- **Depends on:** 2.3

### 4.2 Review-then-escalate wrapper
- **Status:** Todo · **Due:** 2026-11-01 · **Days:** 1.0 · **Label:** WP4
- **Deliverable:** Checker module; block log
- **Depends on:** 4.1
- **Checklist:**
  - [ ] Permitted → passes
  - [ ] First block → flag set, action masked, choose again
  - [ ] Second block → forced escalation, recorded separately

### 4.3 Rule checker tests
- **Status:** Todo · **Due:** 2026-11-01 · **Days:** 0.5 · **Label:** WP4
- **Deliverable:** Test report
- **Depends on:** 4.2

---

## WP5 Baselines and metrics

### 5.1 Simple baselines
- **Status:** Todo · **Due:** 2026-11-01 · **Days:** 0.5 · **Label:** WP5
- **Deliverable:** Initial-symptom, scripted, always-escalate policies
- **Depends on:** 3.3

### 5.2 Threshold policy
- **Status:** Todo · **Due:** 2026-11-08 · **Days:** 1.0 · **Label:** WP5
- **Deliverable:** Posterior-tracking threshold policy
- **Depends on:** 3.3

### 5.3 Metrics module and evaluation runner
- **Status:** Todo · **Due:** 2026-11-01 · **Days:** 1.0 · **Label:** WP5
- **Deliverable:** Metrics module; first results table
- **Depends on:** 3.3, 4.2
- **Checklist:**
  - [ ] Fixed evaluation incident set
  - [ ] Decision quality, investigation cost, escalation, compliance

---

## WP6 Agent training

### 6.1 DQN wired to simulator and rule checker (with masking)
- **Status:** Todo · **Due:** 2026-11-08 · **Days:** 1.0 · **Label:** WP6
- **Deliverable:** Training script
- **Depends on:** 4.2
- **Checklist:**
  - [ ] Masked action selection
  - [ ] Masked max in the target

### 6.2 Pilot runs: fix rewards, base ambiguity, training length
- **Status:** Todo · **Due:** 2026-11-08 · **Days:** 1.0 · **Label:** WP6
- **Deliverable:** Pilot notes; fixed settings
- **Depends on:** 6.1

### 6.3 Small hyperparameter search
- **Status:** Todo · **Due:** 2026-11-08 · **Days:** 1.0 · **Label:** WP6
- **Deliverable:** Chosen settings (recorded)
- **Depends on:** 6.2

### 6.4 Train proposed agent, 10 seeds
- **Status:** Todo · **Due:** 2026-11-08 · **Days:** 1.0 · **Label:** WP6, Milestone
- **Deliverable:** Ten saved models; learning curves
- **Depends on:** 6.3
- **Checklist:**
  - [ ] **M3 reached (with 6.5)**

### 6.5 Train unconstrained and penalty-only agents
- **Status:** Todo · **Due:** 2026-11-08 · **Days:** 1.0 · **Label:** WP6
- **Deliverable:** Saved models; learning curves
- **Depends on:** 6.3

---

## WP7 Experiments and analysis

### 7.1 Experiment 1: agent vs six baselines
- **Status:** Todo · **Due:** 2026-11-15 · **Days:** 1.0 · **Label:** WP7
- **Deliverable:** Main results table
- **Depends on:** 6.4, 6.5

### 7.2 Experiment 2: effect of the rule checker
- **Status:** Todo · **Due:** 2026-11-15 · **Days:** 1.0 · **Label:** WP7
- **Deliverable:** Compliance table and chart
- **Depends on:** 6.5

### 7.3 Experiment 3: ablations (no checks / no escalation)
- **Status:** Todo · **Due:** 2026-11-15 · **Days:** 1.5 · **Label:** WP7, Milestone
- **Deliverable:** Ablation table
- **Depends on:** 6.3
- **Checklist:**
  - [ ] **M4 reached (with 7.1, 7.2)**

### 7.4 Sensitivity to escalation cost
- **Status:** Todo · **Due:** 2026-11-15 · **Days:** 1.0 · **Label:** WP7
- **Deliverable:** Sensitivity table
- **Depends on:** 7.1

### 7.5 Experiment 4: robustness across ambiguity levels
- **Status:** Todo · **Due:** 2026-11-22 · **Days:** 1.5 · **Label:** WP7
- **Deliverable:** Robustness charts
- **Depends on:** 7.1

### 7.6 Analysis: CIs, decision-mix charts, hypotheses
- **Status:** Todo · **Due:** 2026-11-22 · **Days:** 1.5 · **Label:** WP7, Milestone
- **Deliverable:** Figures; findings summary
- **Depends on:** 7.1–7.5
- **Checklist:**
  - [ ] 95% bootstrap CIs over seeds
  - [ ] Findings against H1–H3
  - [ ] **M5 reached (with 8.1)**

### 7.7 Optional: PPO repeat; randomised-ambiguity training
- **Status:** Todo · **Due:** 2026-11-22 · **Days:** 0.5 · **Label:** WP7, Optional
- **Deliverable:** Extra results
- **Depends on:** 7.1

---

## WP8 Working prototype

### 8.1 Replay screen
- **Status:** Todo · **Due:** 2026-11-22 · **Days:** 1.5 · **Label:** WP8
- **Deliverable:** Step-by-step incident replay (checks, proposals, blocks, decision)
- **Depends on:** 6.4

### 8.2 Results panel
- **Status:** Todo · **Due:** 2026-11-29 · **Days:** 1.0 · **Label:** WP8
- **Deliverable:** Comparison tables and charts beside the replay
- **Depends on:** 7.6

### 8.3 Demo script and clean-machine run-through
- **Status:** Todo · **Due:** 2026-11-29 · **Days:** 0.5 · **Label:** WP8
- **Deliverable:** Demo checklist
- **Depends on:** 8.1, 8.2

---

## WP9 Poster and write-up

### 9.1 Draft Chapter 4: implementation and results
- **Status:** Todo · **Due:** 2026-11-29 · **Days:** 1.5 · **Label:** WP9
- **Deliverable:** Chapter 4 draft
- **Depends on:** 7.6

### 9.2 Update Chapters 1–3 with elicitation details and final settings
- **Status:** Todo · **Due:** 2026-11-29 · **Days:** 0.5 · **Label:** WP9
- **Deliverable:** Revised chapters
- **Depends on:** 6.2, 3.7

### 9.3 Research poster
- **Status:** Todo · **Due:** 2026-11-29 · **Days:** 1.5 · **Label:** WP9, Milestone
- **Deliverable:** Poster PDF
- **Depends on:** 7.6
- **Checklist:**
  - [ ] **M6 reached (with 8.3, 9.1)**

### 9.4 Archive code and data; rehearse presentation
- **Status:** Todo · **Due:** 2026-11-29 · **Days:** 0.5 · **Label:** WP9
- **Deliverable:** Archive; rehearsal done
- **Depends on:** 8.3, 9.3

---

## Prompts for Claude with the Trello MCP

Paste these into Claude (Claude Code or Claude Desktop with the Trello connector enabled), with this file attached or available in the working directory.

### Prompt A: Build the board (run once)

```
You have access to a Trello MCP server. Read WBS.md in full before doing anything.

Goal: create my project board from WBS.md, exactly as the "How this file maps to Trello" section describes.

Steps:
1. List the Trello tools available to you and say which ones you will use. If a capability is missing (labels, checklists, due dates), tell me and do the rest.
2. Look for an existing board named "FYP – RL Incident Triage". If it exists, do NOT create a duplicate: update it instead, and never create a second card with the same title.
3. Create the lists in this order: Backlog, This Week, Doing, Waiting on others, Done.
4. Create labels WP0 to WP9, Milestone, Blocked, Optional.
5. For every "### " heading in WBS.md, create one card:
   - Title: the heading text, exactly.
   - List: from Status. Done → Done. Waiting → Waiting on others. Todo → This Week if the Due date falls in the current week (Mon–Sun), otherwise Backlog.
   - Due date: the Due field, at 18:00 Africa/Kampala time.
   - Labels: from the Label field.
   - Description: "Deliverable: …", "Depends on: …", "Days: …", each on its own line.
   - Checklist named "Checklist" with each bullet; tick items marked [x].
6. Do not invent tasks, dates or estimates that are not in WBS.md.
7. When finished, report: number of lists, labels and cards created or updated; any card you could not create and why; and the cards now in "This Week".
```

### Prompt B: Weekly review (every Sunday evening)

```
Using the Trello MCP and WBS.md, do my weekly review for the board "FYP – RL Incident Triage".

1. Read every card's list, due date, checklist and labels.
2. Report:
   - What was completed this week (cards moved to Done, checklist items ticked).
   - Overdue cards (due date passed, not in Done), with how many days late.
   - Cards on the critical path (see WBS.md) that are late or blocked.
   - Whether this week's milestone (M1–M6) was reached, based on its checklist.
3. Move next week's Todo cards from Backlog to This Week.
4. Do NOT change any due date without asking me first. If the plan slips, propose a revised schedule using the cut order in WBS.md, and wait for my approval before applying it.
5. Add a comment to the milestone card with a three-line summary of the week.
6. Draft a 5-line entry I can paste into documentation/progress_log.md.
```

### Prompt C: Quick update (whenever I finish something)

```
Using the Trello MCP, on the board "FYP – RL Incident Triage":
I just finished: <describe what you did>.
Find the matching card(s), tick the relevant checklist items, and move a card to Done only if every checklist item is ticked. If something is blocked, add the "Blocked" label and a comment saying what it is waiting for. Tell me what you changed.
```

### Prompt D: Daily plan (optional, mornings)

```
Using the Trello MCP, look at "This Week" and "Doing" on the board "FYP – RL Incident Triage".
Suggest what I should work on today: at most three cards, critical-path cards first, respecting the "Depends on" field in each card description. Do not change the board.
```
