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
