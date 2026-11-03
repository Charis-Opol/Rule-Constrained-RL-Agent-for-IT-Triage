# Pilot baselines (base level)

Evaluation: 5000 incidents, the same for every policy. Exact expected return 0.390. Ceiling (share resolvable): 71.6%. Pilot data, not Directorate data. n/a: the measure is undefined (for example, F1 for a policy that never escalates).

| Policy | Return | 95% CI | Correct | Wrong | Escalated | Checks | Esc. F1 | Esc. MCC | Blocked proposals | Forced esc. |
|---|---|---|---|---|---|---|---|---|---|---|
| Always escalate | -2.00 | [-2.00, -2.00] | 0.0% | 0.0% | 100.0% | 0.00 | 0.44 | n/a | 0.0% | 0.0% |
| Initial-symptom | -2.00 | [-2.16, -1.84] | 32.7% | 28.6% | 38.7% | 0.00 | 0.34 | 0.01 | 57.6% | 38.7% |
| Scripted (k=9) | -1.08 | [-1.27, -0.90] | 70.6% | 29.4% | 0.0% | 9.00 | n/a | n/a | 0.0% | 0.0% |
| Threshold (tau=0.65) | -0.04 | [-0.21, 0.12] | 60.4% | 19.5% | 20.1% | 4.05 | 0.43 | 0.26 | 5.2% | 0.0% |
| Exact optimal | 0.41 | [0.25, 0.57] | 60.8% | 16.7% | 22.5% | 3.77 | 0.47 | 0.30 | 0.0% | 0.0% |
