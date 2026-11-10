# Comparison experiments (Experiments 1 and 2), fix with verification

Model v2 (pilot developer, Part 2) with `pilot_settings_v3.json`; 5,000 evaluation incidents, the same for every policy; noise 0.1, no missing checks. Baselines run with the safety mechanism and were tuned on 2,000 separate incidents (threshold tau = 0.65, scripted k = 9). Agents: mean over their seeds, with the 95% bootstrap interval over seeds for the return. Unconstrained and penalty-only agents run without enforcement and without the training penalty. Returns in hours (negative = time lost). There is no exact reference with verification. The verification settings are researcher-provisional. Pilot data, not Directorate data.

## Experiments 1 and 2: base level (escalation 120 min)

| Policy | Return | Correct | Any wrong fix | Wrong fixes / incident | Escalated | Checks | Esc. MCC | Rule-breaking proposals | Rule broken (executed) | Compliant success |
|---|---|---|---|---|---|---|---|---|---|---|
| Always escalate | -2.00 | 0.0% | 0.0% | 0.00 | 100.0% | 0.00 | n/a | 0.0% | 0.0% | 0.0% |
| Initial-symptom | -2.33 | 41.3% | 28.6% | 0.42 | 58.7% | 0.00 | 0.21 | 54.7% | 0.0% | 41.3% |
| Scripted (k=9) | -1.38 | 88.3% | 29.7% | 0.41 | 11.7% | 9.00 | 0.53 | 0.0% | 0.0% | 88.3% |
| Threshold (tau=0.65) | -0.38 | 74.1% | 21.4% | 0.26 | 25.9% | 4.72 | 0.57 | 4.7% | 0.0% | 74.1% |
| DQN with safety mechanism (3 seeds) | -0.41 [-0.50, -0.27] | 67.6% | 22.5% | 0.26 | 32.4% | 5.73 | 0.54 | 22.4% | 0.0% | 67.6% |
| DQN unconstrained (3 seeds) | -0.28 [-0.32, -0.23] | 74.7% | 24.9% | 0.30 | 25.3% | 6.05 | 0.55 | 1.1% | 7.6% | 67.9% |
| DQN penalty-only (3 seeds) | -0.24 [-0.33, -0.14] | 74.7% | 25.4% | 0.30 | 25.3% | 4.98 | 0.54 | 0.0% | 0.0% | 74.7% |

**Paired difference in return against the threshold policy** (same incidents; 95% bootstrap over incidents):

- DQN with safety mechanism minus threshold: seed 0: +0.114 [-0.023, +0.241]; seed 1: -0.123 [-0.280, +0.020]; seed 2: -0.092 [-0.240, +0.059]
- DQN unconstrained minus threshold: seed 0: +0.092 [-0.049, +0.223]; seed 1: +0.057 [-0.083, +0.192]; seed 2: +0.150 [+0.015, +0.283]
- DQN penalty-only minus threshold: seed 0: +0.144 [+0.005, +0.283]; seed 1: +0.238 [+0.091, +0.390]; seed 2: +0.047 [-0.089, +0.178]

## Experiment 1, sensitivity: cost of escalation

The shielded agent is retrained at each cost; the threshold and scripted baselines are re-tuned. The wrong-fix cost stays 5x escalation.

### Escalation 60 min (tau = 0.55, k = 9)

| Policy | Return | Correct | Any wrong fix | Wrong fixes / incident | Escalated | Checks | Esc. MCC | Rule-breaking proposals | Rule broken (executed) | Compliant success |
|---|---|---|---|---|---|---|---|---|---|---|
| Always escalate | -1.00 | 0.0% | 0.0% | 0.00 | 100.0% | 0.00 | n/a | 0.0% | 0.0% | 0.0% |
| Initial-symptom | -0.43 | 41.3% | 28.6% | 0.42 | 58.7% | 0.00 | 0.21 | 54.7% | 0.0% | 41.3% |
| Scripted (k=9) | 0.34 | 88.3% | 29.7% | 0.41 | 11.7% | 9.00 | 0.53 | 0.0% | 0.0% | 88.3% |
| Threshold (tau=0.55) | 1.08 | 82.2% | 31.6% | 0.41 | 17.8% | 3.01 | 0.56 | 10.7% | 0.0% | 82.2% |
| DQN with safety mechanism (3 seeds) | 0.92 [0.87, 0.96] | 78.2% | 30.6% | 0.37 | 21.8% | 5.66 | 0.54 | 20.9% | 0.0% | 78.2% |

- DQN with safety mechanism minus threshold: seed 0: -0.209 [-0.314, -0.108]; seed 1: -0.160 [-0.255, -0.052]; seed 2: -0.118 [-0.226, -0.013]

### Escalation 240 min (tau = 0.8, k = 9)

| Policy | Return | Correct | Any wrong fix | Wrong fixes / incident | Escalated | Checks | Esc. MCC | Rule-breaking proposals | Rule broken (executed) | Compliant success |
|---|---|---|---|---|---|---|---|---|---|---|
| Always escalate | -4.00 | 0.0% | 0.0% | 0.00 | 100.0% | 0.00 | n/a | 0.0% | 0.0% | 0.0% |
| Initial-symptom | -6.14 | 41.3% | 28.6% | 0.42 | 58.7% | 0.00 | 0.21 | 54.7% | 0.0% | 41.3% |
| Scripted (k=9) | -4.81 | 88.3% | 29.7% | 0.41 | 11.7% | 9.00 | 0.53 | 0.0% | 0.0% | 88.3% |
| Threshold (tau=0.8) | -2.64 | 53.0% | 9.4% | 0.10 | 47.0% | 7.02 | 0.51 | 1.5% | 0.0% | 53.0% |
| DQN with safety mechanism (3 seeds) | -3.19 [-3.49, -2.98] | 51.9% | 14.6% | 0.15 | 48.1% | 6.19 | 0.51 | 30.5% | 0.0% | 51.9% |

- DQN with safety mechanism minus threshold: seed 0: -0.851 [-1.056, -0.657]; seed 1: -0.459 [-0.657, -0.267]; seed 2: -0.337 [-0.547, -0.134]

