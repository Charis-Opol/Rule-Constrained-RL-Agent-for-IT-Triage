# Chapter Three: Design Decisions and Verification Notes

Working notes for `Chapter_Three.tex`. Not for submission.

## 1. Decisions you made

- Scale: 25 causes, 20 diagnostic checks, 10 operational rules.
- Blocked proposals: reviewed once by the agent; a second block escalates the incident.
- The Directorate of University ICT Services has agreed to support the study. The NDA is not mentioned in any chapter, as you asked.
- Metrics are the standard ones from the reviewed literature.

## 2. Design choices I made that need your approval

These are written into the chapter as the plan. Change any of them before you start building.

| Choice | What the chapter says | Why |
|---|---|---|
| Research design | Design-and-evaluate (design science), experiments in simulation | Fits the "how can / how well" research questions |
| One remedy per cause | 25 recommend actions, one per cause; 46 actions in total | Keeps the model reviewable |
| Single cause, static check results | Stated as simplifying assumptions | Lets the evidence vector serve as the full state, so no recurrent network is needed |
| Likelihood model | Probability of a positive result for each check and cause, elicited as expert judgements | The only parameters the simulator needs |
| Incident context | Attributes such as production system and priority, visible to the agent | The rules need something to refer to |
| Reward | Correct > escalate > wrong; each check has a cost; values set in pilot runs | Chapter One's costs; numbers deliberately not fixed yet |
| Ambiguity controls | Missing probability, noise probability, overlap parameter, with planned ranges | One control per source of ambiguity identified in Chapter Two |
| "Should escalate" label | Rule-prohibited remedy, or the best guess with all available checks is still wrong | Needed for escalation precision and recall; has no tunable threshold |
| Algorithms | DQN and PPO from Stable-Baselines3 | Two algorithm families; DQN matches the closest studies |
| Two training regimes | Base level only, and randomised ambiguity | Separates robustness from exposure during training |
| Blocked step | Consumes a step with no reward; blocked action removed for the next choice; a blocked flag is added to the observation | Implements your review-then-escalate rule so the agent can learn from it |
| Escalation never prohibited | Stated explicitly | Guarantees a permitted action always exists |
| Step limit | Reaching it ends the episode as an escalation, counted separately | Prevents endless investigation |
| Simulated technician | Always resolves an escalated incident, at a fixed cost | Simplest model; listed as a limitation |
| Seeds and statistics | Ten seeds, 95% bootstrap confidence intervals | Reporting practice from Agarwal et al. |
| Baselines | Six policies and two ablations | One per approach in Chapter Two |

## 3. Things the chapter leaves open on purpose

- **The Directorate's exact contribution.** The chapter says the elicitation may use consultation with technicians, anonymised incident records, or both, "subject to the agreement reached". Replace this once the arrangement and the NDA are settled.
- **Numerical reward values, the base ambiguity level, hyperparameters, training length and the number of evaluation episodes.** All are to be fixed in pilot runs and reported in Chapter Four.
- **Number of symptom indicators and context attributes.** To come from the elicitation.
- **Time plan and budget.** Not included. Add them if your department's template requires them.

## 4. Changes made to Chapter One at the same time

- **H2** now reads: the agent with the mechanism "will achieve a higher rate of rule-compliant correct recommendations than the same agent operating without the mechanism". The old wording (fewer violations) was true by construction.
- **Conceptual framework** text and Figure 1.1 now show the review-then-escalate rule.
- **Scope** now states the scale (25 causes, 20 checks, 10 rules), drops "provisionally" from the four categories, and says the Directorate has agreed to support the study.
- **Definition of safety mechanism** mentions the review-then-escalate rule.

## 5. Reference verification

- Six references are new in this chapter. Mnih et al. and Hevner et al. were confirmed against Crossref; Schulman et al., Towers et al. and Agarwal et al. against arXiv; Raffin et al. against the JMLR site.
- I did not re-read these six for this chapter. The claims attached to them are general: what DQN and PPO are, what Gymnasium and Stable-Baselines3 provide, that design science builds and evaluates artefacts, and that results should be reported over several seeds with confidence intervals.
- Hevner et al.: Crossref gives pages 75–106; many citations give 75–105.
- Studies read at abstract level only are still Alauthman et al., Hammar and Li, Hammar et al., Kim and Dan, and D'Antonio and Xie.
- Chapter Three has its own 28-entry reference list so that it compiles alone.

## 6. Not done

- **Not compiled.** No LaTeX distribution is installed on this machine. The file passes structural checks: balanced braces and environments, all citation keys and cross-references resolved.
- No Markdown or Word copy of Chapter Three.
- No code has been written.

## 7. Revisions of 14 October 2026 (agent inputs and elicitation)

- **Why DQN (Section 3.4):** the claim that DQN was "the algorithm of choice in the studies closest to this one" was removed. Algorithms in the reviewed papers are mixed: Q-learning methods in the incident-handling studies (Dunsin, Ren, Alauthman), PPO-family methods in recent shielding and deferral work (Yang, Hamel-De le Court, Könighofer, FALCON). The paragraph now gives three reasons for DQN, says why CPO and PPO-Lagrangian were not adopted, and keeps PPO as the secondary learner.
- **Masking:** the Stable-Baselines3 DQN documentation says it is plain DQN without extensions, and does not list action masking; sb3-contrib documents masking only for MaskablePPO (checked 14 Oct 2026). The chapter now says masking of blocked actions and of already-requested checks is implemented on top of the library.
- **Repeated checks are masked** (your decision).
- **Observations:** symptoms take three values (present, absent, not reported); checks keep four. A paragraph on the numeric encoding (one-hot, 0/1 flags, step count divided by the limit) was added, plus a contrast with the history-based inputs of Ren, Alauthman and FALCON.
- **Alshiekh et al. quotation used:** "the learner has access to the state of the shield and can base its actions on it" (from the PDF in `Papers/`).
- **Alauthman et al. is still abstract-only.** The new sentence on "short telemetry and alert history" quotes its abstract. Read the full text before submission.
- **Elicitation:** now also asks for the remedy per cause, context attributes, symptom–cause likelihoods, cause frequencies and check costs, and (optionally) escalation vs wrong-remedy costs and check unavailability. The likelihoods use a five-point verbal scale mapped to 0.05 / 0.25 / 0.5 / 0.75 / 0.95; this mapping is my proposal, not taken from a source. Cite an elicitation reference if your supervisor expects one.
- **New assumption:** symptoms arrive as structured indicators; free-text extraction is out of scope.
- Compiled with Tectonic: no errors, no unresolved citations.
