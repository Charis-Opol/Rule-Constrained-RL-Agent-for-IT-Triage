# Pilot Experiment Plan

**Goal:** a working proof of concept and first experiment before the Directorate elicitation on Wednesday 4 Nov 2026.
**Input:** `research/elicitation/private/Pilot Elicitation Workbook Responses.xlsx` (not tracked), loaded into `experiments/pilot/pilot_model.json`, one developer with 3 years' experience, dated 2 Nov 2026.
**Status of the results:** pilot only. They show that the method runs and learns. They are not Directorate data and are not thesis findings.

## 1. What the responses give us

| Item | Pilot | Notes |
|---|---|---|
| Causes | 8 | Database 3, Application 2, Infrastructure 2, Authentication 1 |
| Checks | 10 | 6 Low, 3 Medium, 1 High effort |
| Symptoms | 4 | |
| Rules | 5 | 4 on production, 1 on high priority |
| Ratings | 112 of 112 | No blanks; every rule's remedy and check matches the other tabs |
| Costs | 120 min per escalation; a wrong fix is 5x worse | |

Pre-training checks, from `experiments/pilot/pilot_diagnostics.py`:

| Share of incidents the most probable cause gets right | No noise | Noise 0.1 | Noise 0.2 |
|---|---|---|---|
| Prior only | 18% | 18% | 18% |
| Symptoms only | 51% | 51% | 51% |
| Symptoms and all 10 checks (the ceiling) | 82% | 72% | 63% |

The linear prior weights (2, 3, 4) move the no-noise ceiling only from 82% to 80%, so the prior choice is not critical.

Exact optimal policy, with the settings in Section 3 and no missing checks:

| Noise | Return | Correct | Wrong | Escalated | Checks per incident |
|---|---|---|---|---|---|
| 0.0 | 1.67 | 78% | 15% | 8% | 4.3 |
| **0.1 (base)** | **0.39** | **61%** | **17%** | **22%** | **3.8** |
| 0.2 | -0.45 | 46% | 16% | 38% | 2.9 |

Reference points at the base level:

| Policy | Return |
|---|---|
| Always escalate | -2.00 |
| Symptoms only, recommend or escalate (ignores rules) | -1.21 |
| Threshold policy, tuned threshold 0.65 (Phase 3, measured) | -0.04 (95% CI -0.21 to 0.12) |
| Exact optimal | +0.39 |

The threshold estimate is a quick simulation that wrongly counts some later blocks as forced escalations, so the Phase 3 version may score a little higher.

## 2. What this means

### Environment

- **Size:** 19 actions (10 checks, 8 fixes, escalate). The evidence vector has 58 inputs: 40 checks, 12 symptoms, 4 context, 1 step count, 1 blocked flag. With the action mask appended, the network sees 77.
- **Read from configuration:** nothing about the model is hard-coded, so Wednesday's data replaces the pilot file without code changes.
- **Rules can be unlocked:** all five forbid a fix until a named check is observed, whatever its result. So "observed" must be defined exactly: an unavailable check does not count, and a reversed result does.
- **Should-escalate label:** because every rule can be unlocked, no incident counts as "prohibited by the rules" unless the named check is unavailable. With no missing checks, the label contains only irreducibly ambiguous incidents (28% at the base level).
- **Overlap control off:** authentication has only one cause, which the overlap control cannot move, and the other categories have 2 or 3. The causes already overlap, so keep it at 0 in the pilot.
- **Priority:** only High appears in a rule, so Low and Medium behave identically. Keep all three to match Chapter 3.
- **Scripted baseline:** no check order by category was collected, so use the Chapter 3 fallback (most informative first) and report it.
- **Reading the workbook:** read the likelihood tabs and Scale, not the probability tabs. Those were saved as array formulas, although their values are correct.

### Agent

- **Keep:** masked DQN with two hidden layers of 128 units, as in `documentation/manual/code/masked_dqn.py`.
- **Discount of 1.0:** the exact solution is undiscounted, and the comparison needs to be like for like.
- **Main training risk:** 9 of the 19 actions end the episode, so random exploration rarely gets deep into an investigation, and the -10 penalty pushes early learning towards always escalating. Purely random play reaches four checks in only about 5% of episodes, while the optimal policy uses 3.8 on average. Mitigate with check-biased exploration (80% of random actions are checks), a longer exploration schedule, rewards divided by 10 during training and a target update every 1,000 steps. Add one change at a time on tuning seeds and apply the final settings to all three agents. Do not add reward bonuses for running checks.
- **Exact benchmark:** at 3^10 evidence states the problem can be solved exactly, so the agent's gap from the best possible score can be measured. This is not possible at 20 checks.
- **Rules:** the named check is always the strongest check for that remedy (0.95), so obeying the rules costs the optimal policy almost nothing (0.39 against 0.40). Without enforcement it would still break a rule in about 8% of incidents. Expect the safety mechanism to show up in violations, not in return.

## 3. Settings for the pilot

Researcher-set values must be reported as such.

| Setting | Value | Source |
|---|---|---|
| Correct fix reward | +5 | Researcher; gives a real mix of all three outcomes |
| Escalation cost | -2 (120 min, in expert hours) | Response |
| Wrong fix cost | -10 (5x escalation) | Response |
| Check cost, Low / Medium / High | 5 / 15 / 30 min (0.08 / 0.25 / 0.50) | Researcher |
| Prior weights, Rare / Occasional / Common | 1 / 2 / 4 | Researcher |
| P(production) | 0.8 | Researcher |
| Priority, Low / Medium / High | 0.3 / 0.5 / 0.2 | Researcher |
| Base noise, missing, overlap | 0.1, 0, 0 | Researcher |
| Sweep (Phase 5) | Noise 0, 0.1, 0.2; missing 0, 0.2, 0.4 | Subset of Chapter 3 ranges |
| Step limit | 12 (all checks, one block, one decision) | Researcher |

## 4. Phases

Hours are estimates, and DQN training speed has not been measured on this machine. Each phase has a gate that must pass before the next one starts.

### Phase 0: Set up and freeze the data (1 h) - done

- Install `gymnasium`, `stable-baselines3` and `sb3-contrib`, which are not currently installed.
- Create `src/sim/`, `src/rules/`, `src/agents/`, `experiments/pilot/` and `results/pilot/`.
- Move the responses file to `research/elicitation/private/`, because it contains the respondent's name.
- Write a loader that produces `experiments/pilot/pilot_model.json`, with no personal details.

**Gate:** the JSON has 8 causes, 10 checks, 4 symptoms and 5 rules, and matches the probability tabs.

### Phase 1: Environment (3 h) - done

- Build the Gymnasium environment on the toy version in `documentation/manual/code/toy_triage_env.py`, with sizes taken from the configuration.
- Add symptoms, context, noise and missing checks.
- Add reference labels and outcome logging.

**Gate:** `check_env` passes and the same seed gives the same incident. Simulated rates match the ratings. Recommending the most probable cause after all checks scores 82% with no noise and 72% at noise 0.1.

### Phase 2: Safety mechanism (1.5 h) - done

- Read the five rules from the configuration, separately from the agent.
- Implement review-then-escalate: a block uses a step with no reward, sets the flag and masks that action for the next step. A second consecutive block forces an escalation.

**Gate:** tests cover each rule with its check observed, not observed and unavailable. Rules are ignored in the wrong context, escalation is never blocked, and no prohibited action ever executes.

### Phase 3: Baselines, metrics and exact reference (2 h) - done

- Baselines: always escalate, symptoms only, scripted, threshold (threshold tuned on separate seeds).
- Exact optimal policy, adapted from `pilot_diagnostics.py`.
- Evaluation runner: the same fixed 5,000 incidents for every policy, reporting all four groups of measures from Chapter 3.

**Gate:** the exact policy, run through the real environment, scores 0.39 within sampling error, and always-escalate scores exactly -2. A mismatch means a bug in the environment, so stop and fix it. No policy may beat the ceiling or the exact return.

### Phase 4: First DQN (3 h)

- Train one seed with the safety mechanism, starting at about 300,000 steps. Adjust exploration, reward scale and target update interval if it stalls.
- Every 10,000 steps, evaluate on fixed incidents without exploration. Plot return, outcome mix, checks per incident and blocked proposals, and compare the learned starting value with the exact 0.39.
- Warning signs: over 80% escalated or under 1 check per incident after 100,000 steps; or a wrong-fix rate well above 17% with a learned value above 0.39, which points to overestimation (try Double DQN).

**Gate:**

- **Must:** beats symptoms only (-1.21), runs checks, and does not collapse into always escalating.
- **Target:** at or above the threshold policy (-0.04, measured in Phase 3), and closer to the exact 0.39.
- **If it misses the must:** stop and diagnose it. Do not start Phase 5.

**Phase 4 results (3 Nov 2026), tuning seed 100, 1,000 monitoring incidents per point:**

| Run | Final return | Checks | Learned start value |
|---|---|---|---|
| DQN, 300k | -0.73 | 6.6 | 1.74 |
| Double DQN, 300k | -0.60 | 5.7 | 1.11 |
| Double DQN, 1M (exploration to 150k) | -0.27 (flat from about 450k) | 5.3 | 0.99 |
| References | threshold -0.14, exact 0.40 | exact 3.7 | exact 0.39 |

The must-pass gate holds in all three runs. The target, matching the threshold policy, is not met, although the gap is within the monitoring noise. Double DQN and longer training each helped, and gains stop at about 450k steps. The agent still over-checks and overvalues the start of an incident. Blocked proposals rise slowly late in training (about 15% to 25%), because a block costs nothing but a step. Runs 2 and 3 are identical over their first 300k steps, which confirms reproducibility. Figure: `results/pilot/figures/phase4_runs.png`.

### Phase 5: Preliminary experiment (2 h, mostly compute) - done

**Phase 5 results (3 Nov 2026).** Double DQN, 500k steps, exploration to 150k, seeds 0-4; 5,000 evaluation incidents at the base level, 2,000 per sweep level. Tables: `results/pilot/phase5.md`; figures: `results/pilot/figures/phase5_*.png`.

| Policy | Return [95% CI over seeds] | Correct | Wrong | Escalated | Checks | Rule broken (executed) |
|---|---|---|---|---|---|---|
| Threshold (0.65) | -0.04 | 60.4% | 19.5% | 20.1% | 4.05 | 0% |
| Exact optimal | 0.41 | 60.8% | 16.7% | 22.5% | 3.77 | 0% |
| DQN with safety mechanism | -0.28 [-0.34, -0.22] | 51.5% | 15.3% | 33.2% | 4.80 | 0% |
| DQN unconstrained | -0.23 [-0.31, -0.16] | 58.8% | 18.8% | 22.4% | 5.63 | 6.3% (seeds 0.2% to 13.9%) |
| DQN penalty-only | -0.29 [-0.32, -0.24] | 57.9% | 18.9% | 23.2% | 5.67 | 0% |

1. All three agents learned to investigate, recommend and escalate, and all beat the initial-symptom, scripted and always-escalate baselines.
2. No agent reached the threshold policy; all are about 0.65 below the exact optimum.
3. The mechanism gave zero executed violations at every level. Its return cost against the unconstrained agent (-0.28 against -0.23) is within the seed intervals. The penalty-only agent also had zero at the training level, but broke rules in 4.3% of incidents at 20% missing checks and 7.3% at 40%, conditions it was not trained on. The mechanism stayed at 0%.
4. Under the mechanism, blocked proposals fall from about 35% to about 20% and then stay there: the agent relies on being stopped, because a block costs only a step. The penalty-only agent stops proposing violations within 25k steps.
5. As noise rises, every agent escalates more but keeps about the same number of checks, unlike the exact policy. The shielded agent degrades least at 20% noise (-0.95 against about -1.2).

- Train three agents with 5 seeds each: with the safety mechanism, unconstrained, and penalty-only (penalty of 10). This is fewer than the thesis's 10 seeds, as the WBS cut order allows.
- Compare them with the baselines and the exact policy on the same incidents, using 95% bootstrap intervals.
- Run the noise and missing-check sweep on the saved agents, without retraining.

Questions it answers:

1. Does the agent learn to investigate, recommend and escalate at sensible rates?
2. How close does it get to the exact optimum, and does it beat the threshold policy?
3. Does the mechanism bring executed violations to zero at little cost in return?
4. Do blocked proposals fall during training?
5. Does the agent investigate or escalate more as noise rises?

**Gate:** results reproduce from the saved configuration and seeds.

### Phase 6: Pilot note and Wednesday (1 h)

- One-page note: setup, results table, one learning curve, limitations, clearly labelled as pilot.
- Take the questions in Section 5 to the elicitation.

### Phase 7: Natural-language input and prototype (added 3 Nov 2026, at the lecturer's request)

**Goal:** a prototype that takes a ticket written in ordinary language and the logs that go with it, and returns investigate, recommend or escalate, with its reasons. A language model reads the input; the trained agent still decides.

**Design.** Four stages, each replaceable on its own:

| Stage | Does | Built from |
|---|---|---|
| 1. Reader | Turns the ticket and logs into a fixed form: category (the topic), one-line summary, each symptom (present, absent, not mentioned), each context attribute, and each check's result (positive, negative, not shown), with the quoted line behind every finding | `src/prototype/reading.py` (offline keyword reader), `src/prototype/llm.py` (Claude reader) |
| 2. Agent | The trained DQN from Phase 5 (safety mechanism, seed 0, the best seed at the base level), unchanged. It runs checks one at a time; a check's result is looked up in the form when the agent asks for it, or asked of the operator if the logs do not show it | `src/prototype/triage.py`, `LiveTriageEnv` |
| 3. Safety mechanism | Unchanged from Phase 2: every proposal is checked against the five rules, with review-then-escalate | `src/rules/safety.py` |
| 4. Output | A recommendation that a person applies, or an escalation with a handover: what was checked, what each check showed, and the most probable causes from the ratings | `src/prototype/cli.py`, dashboard "Prototype" view |

**Why the language model does not decide.** This answers the Directorate's question of how the project differs from passing error logs to an AI coding agent. The language model does what it is good at, reading free text, and fills in a form whose fields come from the scenario model. Its output is constrained by a JSON schema, so it cannot propose a fix or an escalation. Deciding when to gather more evidence, act or escalate, under check costs and rules, stays with the agent that was trained and evaluated for it, and the rule checker stays independent of both. The form is built from `pilot_model.json`, so the Directorate model replaces it without code changes.

**Safeguards.**

- **Evidence must exist.** A language-model finding whose quote is not in the ticket or logs is discarded and shown as a warning.
- **Unknown context is strict.** Context the ticket does not state defaults to production and high priority, which switches the rules on.
- **Symptoms not mentioned count as absent,** as in training.
- **Offline by default.** The keyword reader is the default and sends nothing anywhere. The Claude reader removes e-mail addresses, phone numbers, IP addresses and tokens before sending, and must not be used on real Directorate tickets without the Directorate's approval (Section 5, question 6).
- **Recommend only.** The prototype never applies a fix.
- **Language-model settings:** `claude-opus-5-5`, effort `low` (form filling, not reasoning), structured output, and the server-side refusal fallback. A refusal or a cut-off answer is an error, never an empty form.

**Built (3 Nov 2026):** the readers, the live environment, the command line (`python -m src.prototype.cli --ticket ... --logs ... [--reader claude] [--ask]`), the dashboard view, six fictional cases in `prototype/examples/` with the researcher's expected reading, `experiments/pilot/prototype_config.json` (keywords, log patterns, thresholds and defaults, all researcher-set), `experiments/pilot/evaluate_prototype.py`, and 31 tests in `tests/test_prototype.py`.

**First results (3 Nov 2026), keyword reader:** `results/pilot/prototype.md`.

| Case | Written to show | Agent's decision |
|---|---|---|
| sign_in | C08 | Recommend C08, no checks |
| transcript_duplicates | C07 | Recommend C07 after the mechanism blocked it until D10 was run |
| payment_gateway | C01 | Recommend C01 after the mechanism blocked it until D01 was run |
| results_approval | C02 | Forced escalation: proposed C02 before running D05, then C03 |
| fees_release | C06 | Recommend C07 (wrong): never ran D09, which the logs show positive |
| vague_slow (no logs) | Escalate | Recommend C04 after five checks came back unavailable |

1. **The pipeline works end to end,** and no prohibited fix got through in any case.
2. **The keyword reader matched the researcher's reading on every field** except category (2 of 6 wrong). This is not evidence of accuracy, because the same person wrote the keywords and the cases.
3. **The mistakes come from the agent, not the reader.** The agent makes the same decision from the researcher's expected reading in all six cases.
4. **It leans on the mechanism.** In five of six cases it proposed a prohibited fix before the check that would allow it, as in Phase 5 (finding 4).
5. **Missing evidence is the weak point.** The agent was trained with no missing checks, so a check the logs do not show is new to it. With no logs it recommended a fix where it should have escalated.

**Gate:**

- **Must (met):** tests pass; no prohibited fix is ever recommended; every finding traces to a quoted line; it runs offline.
- **Target (to do):** the steps below.

**Still to do:**

1. **Reader test on unseen tickets.** 20 to 30 tickets with logs, written by someone other than the researcher (for example the pilot developer), each with an expected reading. Compare the keyword and Claude readers field by field. Report check results separately, because they drive the agent. This is where the language model should earn its place: the keyword reader only knows the phrasings it was given. Run with `python -m experiments.pilot.evaluate_prototype --claude`.
2. **Train with missing checks.** Retrain the shielded agent with the missing-check rate drawn from 0 to 0.4 in each episode (the randomised training listed as optional in WBS 7.7). In the prototype, missing checks are the normal case, not the stress test. Re-run the Phase 5 base table and the six cases.
3. **A block that costs something.** At present a block costs only a step, so the agent proposes first and checks later. Charging a block like a Low check would change the Chapter 3 design, so agree it with the supervisor first and report it as an ablation, not a quiet fix.
4. **Directorate log format.** The log patterns fit the example format only. They need rewriting for the Directorate's API console and Grafana output (Section 5, question 6), or the Claude reader can be relied on for logs.
5. **Write-up:** the four stages as one figure for Chapter 3 and the poster, and the reader test and the six cases in Chapter 4.

**Limits:** six cases written by the researcher show that the pipeline works, not how accurate it is. The agent and the rules are the pilot ones (one rater). Choosing seed 0 because it scored best on the evaluation incidents is a selection on test data; that is acceptable for a demonstration, but not for reported results.

### Phase 8: Agent as a decision layer: delegate, draft pull requests, routed escalation (added 9 Nov 2026)

**Goal:** the user's extension of the lecturer's request. Ticket -> language-model reader (topic, symptoms, context) -> RL agent -> action, where the action can be to investigate (a check), to **delegate** a heavy analysis to a language model, to **fix** a code fault through a draft pull request that a person reviews, or to **escalate** with a full report to the person in charge.

**Where the line is.** The evaluated core is everything that produces the discrete decision: `src/sim`, `src/rules`, `src/agents`, the model and settings files, and the experiments. Everything before the decision (reading) and after it (carrying it out) is the demo layer in `src/prototype/`. The demo layer imports the core; the core never imports the demo layer.

| Part | Where | Core or demo |
|---|---|---|
| Overlap control omega, Chapter 3 formula | `src/sim/scenario.py` (`apply_overlap`, settings key `overlap`, default 0) | Core. With omega = 0 every Phase 5 result is unchanged (tested) |
| Pilot model v2: D11 "Full log analysis (delegated)", High effort; per cause `code_fault` and `owner` (a role) | `experiments/pilot/build_model_v2.py` -> `pilot_model_v2.json`, `pilot_settings_v2.json` (step limit 13) | Core input. `pilot_model.json` is untouched, so Phase 5 reproduces |
| Delegated check | `src/prototype/delegate.py` | Demo. The agent picks D11 like any check and pays its cost; a fixed template asks one question; the answer is reduced to positive / negative / not shown with a verified quote. The written report goes to the person, never into the observation |
| Draft pull request, notice, routed escalation | `src/prototype/actions.py` | Demo. Acts only after the decision |
| Toy repository with four planted bugs (C01, C04, C05, C08) and pre-written fixes | `prototype/toy_repo/`, `prototype/toy_repo_fixes/` | Demo. Fictional |
| Part 2 workbook for the pilot developer | `research/elicitation/Pilot_Elicitation_Workbook_Part2.xlsx` (`make_part2_workbook.py`) | Input |

**Delegation is option (a): a check in the model.** Being expensive is its High effort. Being noisy is its likelihood ratings, which are less extreme than a direct check's. So the agent learns from training when delegating is worth the cost, and the result is part of what is evaluated. No environment code changed. The action space grows from 19 to 20 + 1 (11 checks, 8 fixes, escalate) for v2.

**Why "fix" does not weaken the guarantee.** A draft pull request is not a new action. It is how a permitted "recommend the fix for cause j" is carried out when cause j is marked as a code fault. The safety mechanism decides at the cause level exactly as before. On top of that, `actions.py` enforces, with tests in `tests/test_extension.py`:

1. **Re-confirmation.** It acts only on a recommendation that `triage()` has checked against the rules a second time, on the final evidence (`permitted`).
2. **Code faults and drafts only.** A pull request is opened only for a cause marked `code_fault`, and only as a draft.
3. **Existing source files only.** A patch may change only an existing source file, not the tests, a new file or a path outside the repository.
4. **Fixed command list.** Only these commands can run: git init, add, commit, checkout, clone, push of a new branch, and `gh pr create --draft`. There is no merge, and no push to main.
5. **Tests gate.** The repository's tests run before and after the patch. The patch must make at least one failing test pass and break none, or no pull request is opened and the owner gets a notice instead.

State the limit plainly in the thesis: **the rules cover the decision to fix a cause, not the content of the patch.** Whether a patch is correct is for the human reviewer. Also, a language-model patch is code that runs on this machine during the test step. That is acceptable for the toy repository only; a real deployment would run it in CI.

**Routing.** A recommendation goes to the owner of its cause. An escalation goes to the owner of the most probable cause if that cause reaches 50%, and otherwise to the fallback owner (the senior developer, as in the interview: "assigned to the senior developer if unknown"). Messages are written to `results/pilot/outbox/` and are not sent anywhere.

**Error rates for p_noise and p_miss.** `evaluate_prototype.py` now reports, over every check result: reversed (compare p_noise), missed (compare p_miss) and invented (not modelled in the simulator), for the reader and for the delegate separately. Reader error informs p_noise and p_miss only. **Omega is not a reader error:** it is the overlap between causes in the world, and it stays a simulator setting that Experiment 4 sweeps. Only the developer's sample tickets (Part 2) measure accuracy; the researcher's cases do not.

**Provisional values.** Until Part 2 comes back, D11's ratings, `code_fault` and `owner` are the researcher's (`pilot_additions_provisional.json`, labelled `researcher-provisional` in the model). To replace them: `python -m experiments.pilot.build_model_v2 --workbook "<returned Part 2>"`, then retrain the v2 agents (about 25 minutes for three seeds in parallel) and re-run `evaluate_prototype --cases prototype/examples/developer --out prototype_developer`.

**First results (9 Nov 2026), provisional D11 ratings.** Three shielded agents trained on v2 with the Phase 5 settings (Double DQN, 500k steps, exploration to 150k), seeds 0-2: `results/pilot/runs/v2_shielded_seed*`. Figures are on the 1,000 training-monitor incidents.

| | Return | Correct | Wrong | Escalated | Checks | Delegates (D11) |
|---|---|---|---|---|---|---|
| Exact optimal, v2 | 0.405 | 62% | 18% | 20% | 3.95 | |
| Exact optimal, v1 (no D11) | 0.39 | | | | | |
| v2 seeds 0 / 1 / 2 | -0.54 / -0.54 / -0.37 | 52-54% | 15-18% | 28-33% | 5.1-6.1 | 28% / 24% / 12% of incidents |
| v1 (Phase 5) shielded seeds 0-4, same monitoring incidents | -0.25 to -0.32 | | | | 4.2-5.3 | |

1. **D11 adds almost nothing under the provisional ratings.** The best possible return rises from 0.39 to 0.405, because a High-effort check whose ratings are mostly Often or Sometimes tells the agent little. The developer's ratings will settle whether delegation is worth its cost. That is a finding, not a defect.
2. **The v2 agents score lower than the Phase 5 agents** (-0.37 to -0.54 against -0.25 to -0.32). One more action and a longer step limit make learning harder at 500k steps. Seed 2 is the demo agent, chosen on the monitoring incidents, not the evaluation ones.
3. **End to end on eight cases** (`results/pilot/prototype_v2.md`). `class_results_slow`: the agent recommended C04, the rule checker re-confirmed it, the pre-written patch fixed its test and broke none, and a draft branch was committed in `results/pilot/demo_repo`, with a notice to the Application team lead. `profile_cache`: escalated to the Infrastructure and containers lead (C05 at 62%). Compared with Phase 7, `results_approval` is now resolved and `payment_gateway` is now escalated. `fees_release` (wrong cause) and `vague_slow` (a fix where it should escalate) are unchanged.
4. **The demo agent never chose D11 on the eight cases.** The delegate path is tested with a scripted agent (`tests/test_extension.py`), not shown by the trained one.
5. **It still proposes before it checks,** up to 6 blocked proposals in one incident. This is Phase 7 finding 4 again, and it argues for the "block that costs something" ablation (Phase 7, still to do, item 3).
6. **Reader error rates are 0% on these cases,** which means nothing: the researcher wrote the cases and the keywords. Only the developer's Part 2 tickets measure them.

**Run it:**

```bat
.venv\Scripts\python -m src.prototype.cli --ticket prototype\examples\class_results_slow\ticket.txt --logs prototype\examples\class_results_slow\logs.txt --act
.venv\Scripts\python -m src.prototype.cli --ticket ... --logs ... --act --pr github                  :: after the one-off GitHub setup
.venv\Scripts\python -m src.prototype.cli --ticket ... --logs ... --reader claude --delegate claude --act --patcher claude   :: needs ANTHROPIC_API_KEY
.venv\Scripts\python -m experiments.pilot.evaluate_prototype                                          :: results/pilot/prototype_v2.md
```

One-off GitHub setup (creates a **private** throwaway repository with the toy app): `python -m src.prototype.actions Charis-Opol/triage-demo-portal`.

### Phase 9: From "recommend" to "fix", and fix with verification (added 9 Nov 2026)

**Decision (user, 9 Nov 2026).** The project's wording changes from "recommend" to "fix" in the thesis, the prototype and the training, and the agent is to learn to fix incidents, not only name a remedy. Step-by-step record: `documentation/phase9_log.md`. Earlier phases above keep their original wording because they record what was done at the time.

**Part A: wording (done 9 Nov 2026).** The terminal action "recommend the fix for cause j" is now "fix cause j" (apply its remedy). In the simulation nothing changes: a fix ends the episode with $r_\text{correct}$ or $-\lambda_\text{wrong}$, exactly as a recommendation did, so the Phase 5 results stand as they are. Renamed: the thesis title (*Investigate, Fix or Escalate*), objectives, RQ2, H2 ("rule-compliant correct fixes"), scope, key terms and the Chapter 3 metrics ("wrong-fix rate"); Figure 1.1; the README; the prototype output (`FIX:`), its decision outcome (`"fix"`), and the non-code action (`fix_order` to the owner, previously `notice`). Citations that describe other work as recommending were left as they are. The scope statement now says what is true: fixes are applied in simulation, and in the prototype only to the fictional toy repository as draft pull requests a person merges.

**Part 2 workbook returned (9 Nov 2026).** The pilot developer's answers replace the provisional values in `pilot_model_v2.json` (`additions_source: pilot developer (Part 2)`). Code-fix flags agree with the provisional ones; owners and D11 ratings changed (D11 is now rated Often or Almost always for C02, C05-C08 and Rarely for C01, C03). The 20 sample tickets are in `prototype/examples/developer/` (git-ignored: some name what look like real endpoints and classes). The v2 agents trained on the provisional values are out of date and are retrained (see the log).

**Part B: fix with verification (code done 9 Nov 2026; training pending).** Opt-in through `experiments/pilot/pilot_settings_v3.json` (`fix_with_verification`); v1/v2 settings are unchanged and the Phase 5 results still reproduce. A fix of cause j costs its apply time $a_j$; if j is the true cause the episode ends with $r_\text{correct} - a_j$, otherwise the agent pays $a_j + h_j$, sees a "fix failed" flag for j (one flag per cause, appended to the observation), j is masked, and the episode goes on. After 2 failed fixes a person takes over (outcome `fix_limit`, counted as an escalation, plus $\lambda_\text{esc}$). Mean harm $= (5 - 1) \times 120$ min, so a wrong fix then escalation costs the elicited 5x on average; the spread follows the rule reasons R01-R05 (C07 deletes 2.0, C02/C06 1.5, C03 1.0, C01 0.75, code fixes C04/C05/C08 0.5). New metrics: `wrong_fix_rate` (incidents with any wrong fix applied) and `mean_wrong_fixes`. The exact solver does not model verification and is skipped. The prototype refuses v3 settings until it has a verification step (for code faults, the toy repository's tests could serve). Chapter 3 has a new subsection, "Fix with Verification". Tests: `tests/test_verify.py`.

**Researcher-provisional:** apply minutes, harm weights, max_failed_fixes 2, max_steps 15, and reliable verification. To be put to the developer in a Part 3 workbook.

**Baselines, 1,000 evaluation incidents, shielded, model v2 with Part 2 values:**

| Settings | Policy | Return | Resolved | Wrong-fix rate | Escalated | Checks |
|---|---|---|---|---|---|---|
| v2 (fix ends episode) | Always escalate | -2.00 | 0% | 0% | 100% | 0.0 |
| v2 | Initial-symptom | -1.99 | 32% | 28% | 40% | 0.0 |
| v2 | Threshold (0.65) | -0.29 | 62% | 24% | 14% | 3.9 |
| v3 (fix + verify) | Always escalate | -2.00 | 0% | 0% | 100% | 0.0 |
| v3 | Initial-symptom | -2.30 | 41% | 28% | 59% | 0.0 |
| v3 | Threshold (0.65) | -0.61 | 75% | 24% | 25% | 4.7 |

A second try lets Threshold resolve more incidents (75% against 62%), but each wrong remedy now does harm, so its return is lower. Threshold was tuned for v2; it is not re-tuned here.

**Train v3:** `train_dqn --agent shielded --model experiments/pilot/pilot_model_v2.json --settings experiments/pilot/pilot_settings_v3.json --steps 500000 --every 25000 --double-q --exploration-steps 150000 --seed N --name v3_shielded_seedN`, seeds 0-2. The monitor has no exact reference line in this mode.

**Total: about 13.5 hours for Phases 0 to 6; Phase 7 so far about 4 hours, with about 1.5 days of remaining work.**

**If time runs short, cut in this order:** the sweep, the penalty-only agent, then seeds from 5 to 3. Never cut the gates in Phases 1 to 3, because they are what make any result believable.

**Out of scope for the pilot:** PPO, randomised training, the two ablations, the overlap sweep, the replay screen, and an exact solution with missing checks.

## 5. Questions to raise on Wednesday

1. **Absolute rules:** are there actions that are never allowed under a condition, whatever has been checked? The pilot has none, which empties that part of the should-escalate label.
2. **Check order:** what order do staff check things in for each category? The scripted baseline depends on this.
3. **Remedy risk:** do wrong fixes differ in cost? The pilot uses one 5x figure for all, though its rule reasons suggest a rollback and an index change carry different risks.
4. **Frequency:** can approximate counts replace the verbal frequency ratings? Otherwise the prior weights remain my assumption.
5. **Dependent checks:** the model assumes checks are independent given the cause, but some probably are not, such as lock-wait errors and long transactions.
6. **Tickets, logs and language models (Phase 7):** what do the ticket tracker, API console and Grafana logs look like? May tickets and logs, with personal details removed, be sent to an external language-model service, or must the model run on university machines?
7. **Sample tickets:** can the Directorate provide anonymised tickets with their logs, or review fictional ones, for testing the reader?

## 6. Limits on what can be claimed

- One rater, not the Directorate, and not an expert review of the model.
- The reward for a correct fix and all the settings marked "Researcher" are assumptions. Only the 120 minutes and the 5x come from the response.
- Doing well at this size does not predict performance on the full model. In particular, the exact solution here will not exist at 20 checks.
- This does not breach the Chapter 3 commitment to fix the model before training, because the Directorate model has not been built yet. Hold to that commitment after Wednesday.
