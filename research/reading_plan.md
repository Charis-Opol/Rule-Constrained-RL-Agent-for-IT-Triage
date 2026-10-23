# Reading Plan

A reading path to ground the whole project: the problem (Chapter 1), the literature (Chapter 2), the method (Chapter 3) and the build (Chapter 4). It lists 21 papers in five stages. Every paper is already cited in the thesis or the systematic review.

**If time is short, read the five ★ papers first.** They are the ones an examiner is most likely to ask about.

Where a PDF is already in the repository, its folder is given:

- `core` = `research/literature/core-papers/`
- `intro` = `research/literature/introduction-papers/`
- `slr` = `research/new-slr-literature/`

"Online" means the paper is not on disk; most of these are freely available.

---

## Stage 1: The problem (Chapter 1, opening of Chapter 2)

- [ ] ★ **Chen et al. (2020)**, *Towards intelligent incident management* (`intro`: "Towards Intelligent Incident Management.pdf")
  - Why: the core evidence that triage is hard. Distinct problems produce similar symptoms.
  - Focus: the definition of incident management and triage, and the findings on diagnosis delays.
- [ ] **Remil et al. (2024)**, AIOps survey for incident management (`intro`: "AIOps Solutions for Incident Management.pdf")
  - Why: defines triage, catalogues the evidence sources, criticises classification metrics, and says that automatic fixes must run safely.
  - Focus: the sections on incident triage, the data sources and evaluation.
- [ ] **Sutton and Barto (2018)**, *Reinforcement Learning: An Introduction* (online; free at incompleteideas.net)
  - Why: the vocabulary you will be examined on.
  - Focus: Ch. 1 (introduction), Ch. 3 (MDPs, return, value), Ch. 6 (Q-learning), and function approximation in Ch. 9.
- [ ] **Kaelbling et al. (1998)**, *Planning and acting in partially observable stochastic domains* (online)
  - Why: hidden cause, belief, and actions taken for the information they give. Your sufficient-statistic argument in §3.4.2 rests on it.
  - Focus: belief states and the value of information-gathering actions.

**Checkpoint:** you can explain in two sentences why triage is a sequential decision under partial observability.

---

## Stage 2: The three decisions and the rules (core of Chapter 2)

- [ ] **Janisch et al. (2019)**, classification with costly features using deep RL (online)
  - Why: the "investigate or decide" half of your decision, and the source of your accuracy-versus-cost curve.
- [ ] **Madras et al. (2018)**, *Predict responsibly: learning to defer* (`intro`: "NeurIPS-2018-predict-responsibly-...pdf")
  - Why: the "decide or hand over" half. Your first ablation (no checks allowed) is built on it.
- [ ] ★ **Alshiekh et al. (2018)**, *Safe reinforcement learning via shielding* (`core`: "Alshiekh et al., Safe RL via Shielding.pdf")
  - Why: the basis of your rule mechanism.
  - Be able to say how yours differs: the rules are written by hand, not synthesised from a model, and the agent gets one re-proposal before escalation.
- [ ] **Könighofer et al. (2025)**, *Shields for safe RL* (`core`: "Shields for Safe RL (CACM 2025).pdf")
  - Why: explains why a reward penalty is not enforcement, which justifies your penalty-only baseline.
- [ ] **Yang et al. (2023)**, *Safe RL via probabilistic logic shields* (`core`: "Yang et al., Safe RL via Probabilistic Logic Shields.pdf")
  - Why: a shield that silently rejects actions can hinder learning, which is why your agent is told about a block.

**Checkpoint:** you can explain why information gathering and deferral have been studied separately, and what shielding guarantees and what it does not.

---

## Stage 3: Closest competitors (read in full; examiners will cite these back at you)

For each paper, write one paragraph: *what it does, and how this study differs.*

- [ ] ★ **Sahin and Mert (2026)**, *Dual-threshold conformal deferral for trustworthy security alert triage* (`slr`)
  - The nearest precedent. It gathers evidence, then escalates or closes an alert, and a separate layer defers uncertain alerts to an analyst.
  - Contains the label-leakage warning behind your leakage check.
  - Difference: your agent recommends a remedy that changes the system.
- [ ] ★ **Kovtun et al. (2026)**, *Risk-sensitive decision-making in SOC alert escalation* (`slr`)
  - The only study that measures all four of your metric groups.
  - Keeps a belief over a hidden state and learns escalation under analyst-capacity constraints.
- [ ] **Okafor (2026)**, *A leakage-free benchmark of offline policy learning for SOC alert triage* (`slr`)
  - Learns to dismiss, investigate or contain alerts.
  - Shows that MCC exposes degenerate policies that F1 and ROC-AUC hide, which is why you report escalation MCC.
- [ ] **Singh (2026)**, *Autonomous AI Decision Control Tower* (`slr`)
  - An IT-operations study with a deterministic rule guard and a hand-off to a person.
  - The nearest precedent for your mechanism. Compliance fell from 99.9% to 72.3% without the guard.
- [ ] **Ravi et al. (2025)**, *SAFE-HGX* (`slr`)
  - A rule shield that substitutes blocked actions, with large measured costs.
  - Read critically: it is weakly rated in the review and inconsistent in places.
- [ ] **Hammar and Li (2025)**, *Online incident response planning under model misspecification* (`slr`)
  - Belief-based incident response; the most robust method under model error.
- [ ] **Hammar et al. (2026)**, *Adaptive network security policies via belief aggregation and rollout* (`slr`)
  - Adapts to system change in seconds where PPO takes minutes. A model for robustness testing.
- [ ] **Alauthman et al. (2026)**, *Explainable RL for automated incident response in critical infrastructure* (`slr`)
  - Read it so you can explain why it was excluded: it reports an evaluation plan and indicative findings, with no measured values.
- [ ] Optional, for the IT-service side:
  - [ ] **Wang et al. (2023)**, *Root cause analysis via hierarchical RL from human feedback* (`slr`)
  - [ ] **Ding et al. (2023)**, *Adaptive, interpretable and efficient root cause analysis* (`slr`)

**Checkpoint:** you can state the research gap in three sentences without saying "no one has done this". Instead, say what the nearest studies do and what they lack.

---

## Stage 4: Method and evaluation (Chapter 3)

- [ ] ★ **Mnih et al. (2015)**, *Human-level control through deep reinforcement learning* (online)
  - Your main learning algorithm.
  - Know experience replay, the target network and ε-greedy exploration.
- [ ] **Geifman and El-Yaniv (2019)**, *SelectiveNet* (`intro`: "A Deep Neural Network with an Integrated Reject Option.pdf")
  - The source of coverage and selective accuracy, and the idea behind your threshold baseline.
- [ ] **Levy et al. (2026)**, *ST-WebAgentBench* (`core`: "ST-WebAgentBench.pdf")
  - Completion under policy, which your compliant success rate is based on.
- [ ] **Pacella et al. (2026)**, floor-safety guardrail for escalation (`core` or `intro`: the floor-safety paper)
  - Escalation recall, and policy-mandated escalation.
- [ ] **Turan (2026)**, escalation rate and realised safety under reviewer overload (`core`: likely "Oversight Has a Capacity...pdf"; check the author before relying on this)
  - Why escalating everything is not safe.
- [ ] **Hevner et al. (2004)**, *Design science in information systems research* (online)
  - Justifies your build-and-evaluate design. Expect a defence question on it.
- [ ] **Page et al. (2021)**, *The PRISMA 2020 statement* (online; open access in BMJ)
  - Needed to defend the systematic review.

**Checkpoint:** for every metric in §3.8, you can name the paper it comes from and say what failure it detects.

---

## Stage 5: Execution (Chapter 4; read just before coding)

- [ ] **Agarwal et al. (2021)**, *Deep RL at the edge of the statistical precipice* (online)
  - How to report results over seeds honestly. The basis for your 10 seeds and bootstrap confidence intervals.
- [ ] **Raffin et al. (2021)**, *Stable-Baselines3* (online; JMLR, open access)
  - Read with the SB3 documentation: DQN and PPO parameters, callbacks, evaluation.
- [ ] **Towers et al. (2024)**, *Gymnasium* (online; arXiv)
  - Read with the Gymnasium documentation: the `Env` API, `reset` and `step`, spaces, and seeding.

**Checkpoint:** you can sketch the environment's `reset` and `step`, and the training loop, from memory.

---

## Suggested order

1. [ ] Chen, then Remil (problem)
2. [ ] Sutton and Barto chapters, then Kaelbling, then Mnih (foundations)
3. [ ] Sahin and Mert, Kovtun, Okafor (competitors; write the "how this differs" notes)
4. [ ] Alshiekh, then Singh and Ravi (the rule mechanism)
5. [ ] Agarwal plus the SB3 and Gymnasium docs (just before coding)

## Still to obtain

- [ ] Sutton and Barto (2018)
- [ ] Kaelbling et al. (1998)
- [ ] Janisch et al. (2019)
- [ ] Mnih et al. (2015)
- [ ] Agarwal et al. (2021)
- [ ] Raffin et al. (2021)
- [ ] Towers et al. (2024)
- [ ] Hevner et al. (2004)
- [ ] Page et al. (2021)
