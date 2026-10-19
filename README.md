# Rule-Constrained Reinforcement Learning for Ambiguity-Aware IT Incident Triage

Final-year research project, BSc Computer Science, Uganda Christian University.
**Author:** Opol Charis · **Supervisor:** [supervisor's name] · **Partner:** Directorate of University ICT Services, Uganda Christian University

## About the project

When an IT incident is reported, its cause is often unclear: evidence is missing, unreliable, or consistent with more than one cause. This project designs and evaluates a reinforcement learning agent that, for each incident, learns when to:

1. **gather more evidence** (request a diagnostic check),
2. **recommend a fix** that the organisation's operational rules permit, or
3. **escalate** the incident to a human expert.

An independent rule-based safety mechanism checks every proposal. A blocked proposal goes back to the agent once; if the second proposal is also blocked, the incident is escalated. The agent (a deep Q-network, with PPO as a secondary check) is trained and evaluated **entirely in simulation**, in an environment built from scenarios elicited from the Directorate: 25 causes, 20 diagnostic checks and 10 operational rules, with controllable levels of missing, unreliable and overlapping evidence. It is compared with six baseline policies on decision quality, investigation efficiency, escalation behaviour and constraint compliance.

**General objective:** to design and evaluate a rule-constrained reinforcement learning agent for ambiguity-aware IT incident triage that learns when to gather additional diagnostic information, recommend permitted actions, or escalate incidents to a human expert.

<details>
<summary>Research questions</summary>

1. How can ambiguous IT incident triage scenarios involving incomplete or conflicting diagnostic evidence be represented in a controlled environment?
2. How can reinforcement learning support decisions about gathering diagnostic information, recommending permitted actions, and escalating incidents to a human expert?
3. How effectively can a rule-based safety mechanism prevent actions that violate predefined operational constraints?
4. How does the proposed approach compare with selected baseline decision policies in decision quality, investigation efficiency, escalation behaviour, and constraint compliance?
5. How robust is the proposed approach when incident evidence is incomplete, conflicting, or increasingly ambiguous?

</details>

## Status (19 October 2026)

| Part | Status |
|---|---|
| Chapter 1: Introduction | Drafted; revised after the stakeholder interview |
| Chapter 2: Literature review | Drafted (thematic review; a systematic review is in progress) |
| Chapter 3: Methodology | Drafted; revised after the stakeholder interview |
| Scenario elicitation | Workbook ready; session with the Directorate pending |
| Simulator, rule checker, agent, experiments | Not started. Planned over six weeks; see [`WBS.md`](WBS.md) |
| Prototype and poster | Planned for Week 6 |

The plan and progress are tracked in [`WBS.md`](WBS.md) (Trello-ready, with prompts for Claude and the Trello MCP) and in [`documentation/progress_log.md`](documentation/progress_log.md).

## Repository layout

```
.
├── README.md
├── WBS.md                         Work breakdown structure and Trello prompts
├── build.bat                      Builds every LaTeX document (Windows)
├── tools/                         Put tectonic.exe here (not tracked)
├── research/
│   ├── thesis/                    The thesis: compile main.tex
│   │   ├── main.tex, main.pdf
│   │   ├── chapters/              chapter1_introduction, chapter2_literature_review, chapter3_methodology
│   │   ├── citations/references.bib   (IEEEtran style)
│   │   └── images/                Figures 1.1 and 3.1
│   ├── elicitation/               Blank scenario-elicitation workbook (.xlsx)
│   ├── literature/                Paper PDFs (not tracked; README lists them)
│   ├── slr-search-exports/        Database exports (not tracked; README describes them)
│   └── archive/                   Superseded standalone chapters and the original Figure 1.1
└── documentation/
    ├── milestone/                 Mid-semester summary, talking points, original six-week WBS
    ├── source-notes/              Per-chapter notes on sources, verification and open decisions
    ├── stakeholder/               Interview findings, proposal, letter (not tracked; confidential)
    └── progress_log.md            Weekly progress log
```

The source notes were written before this reorganisation and use the old paths: `Papers/` is now `research/literature/core-papers/`, `Papers for the introduction/` is `research/literature/introduction-papers/`, `notes/` is `documentation/source-notes/`, and `milestone/` is `documentation/milestone/`.

## Building the documents

All documents are LaTeX and build with [Tectonic](https://tectonic-typesetting.github.io), so no full TeX installation is needed.

1. Download `tectonic.exe` (version 0.17.0 was used) and place it in `tools/`.
2. Run `build.bat`. It builds the thesis (`research/thesis/main.pdf`) and the milestone and stakeholder documents. The first run downloads LaTeX packages, so it needs an internet connection.

To build only the thesis:

```bat
cd research\thesis
..\..\tools\tectonic.exe main.tex
```

The milestone documents need the Trebuchet MS font files (`trebuc.ttf`, `trebucbd.ttf`, `trebucit.ttf`, `trebucbi.ttf`). On Windows, copy them from `C:\Windows\Fonts` into `documentation/milestone/fonts/`.

## What is not in this repository, and why

| Excluded | Reason |
|---|---|
| Paper PDFs (`research/literature/**/*.pdf`) | Publishers' copyright |
| Database exports (`research/slr-search-exports/`) | Database licence terms restrict sharing bulk records |
| Stakeholder material (`documentation/stakeholder/`) | Non-disclosure agreement with the Directorate; names and interview content |
| Completed elicitation data (`research/elicitation/private/`) | Non-disclosure agreement; save completed workbooks there |
| Trebuchet MS fonts | Microsoft licence |
| `tools/tectonic.exe` | 50 MB binary, freely downloadable |

These rules are in [`.gitignore`](.gitignore). If this repository is private and you want any of them versioned, remove the matching lines.

## Data and ethics

The agent is trained and evaluated only in simulation. It is not connected to any university system and takes no action on university infrastructure. The simulator is built from elicited descriptions of incident types, checks, fixes and rules, not from logs, tickets or personal data. No member of staff is identified. Material derived from the Directorate's information is published only where the non-disclosure agreement allows it.

## Use of AI assistance

Claude (Anthropic) was used as a writing and research assistant: drafting and revising chapter text, checking references, building the elicitation workbook and planning documents, and organising this repository. The author reviewed, edited and is responsible for all content. Claims, citations and decisions are recorded in `documentation/source-notes/`.

## Licence

[To be decided. Until a licence is added, all rights are reserved by the author.]
