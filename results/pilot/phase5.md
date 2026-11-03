# Phase 5 results (base level)

5,000 evaluation incidents, the same for every policy; noise 0.1, no missing checks. Agents: mean over their seeds, with the 95% bootstrap interval over seeds for the return. Unconstrained and penalty-only agents run without enforcement and without the training penalty. Pilot data, not Directorate data.

| Policy | Return | Correct | Wrong | Escalated | Checks | Esc. MCC | Blocked or broken proposals | Forced esc. | Rule broken (executed) | Compliant success |
|---|---|---|---|---|---|---|---|---|---|---|
| Always escalate | -2.00 | 0.0% | 0.0% | 100.0% | 0.00 | n/a | 0.0% | 0.0% | 0.0% | 0.0% |
| Initial-symptom | -2.00 | 32.7% | 28.6% | 38.7% | 0.00 | 0.01 | 57.6% | 38.7% | 0.0% | 32.7% |
| Scripted (k=9) | -1.08 | 70.6% | 29.4% | 0.0% | 9.00 | n/a | 0.0% | 0.0% | 0.0% | 70.6% |
| Threshold (tau=0.65) | -0.04 | 60.4% | 19.5% | 20.1% | 4.05 | 0.26 | 5.2% | 0.0% | 0.0% | 60.4% |
| Exact optimal | 0.41 | 60.8% | 16.7% | 22.5% | 3.77 | 0.30 | 0.0% | 0.0% | 0.0% | 60.8% |
| DQN with safety mechanism (5 seeds) | -0.28 [-0.34, -0.22] | 51.5% | 15.3% | 33.2% | 4.80 | 0.23 | 20.7% | 1.6% | 0.0% | 51.5% |
| DQN unconstrained (5 seeds) | -0.23 [-0.31, -0.16] | 58.8% | 18.8% | 22.4% | 5.63 | 0.24 | 1.0% | 0.0% | 6.3% | 54.0% |
| DQN penalty-only (5 seeds) | -0.29 [-0.32, -0.24] | 57.9% | 18.9% | 23.2% | 5.67 | 0.24 | 0.0% | 0.0% | 0.0% | 57.9% |
