# Prototype check (Phase 7, extended 9 Nov 2026)

8 fictional cases (`prototype/examples`), model `experiments/pilot/pilot_model_v2.json`, agent `results/pilot/runs/v3_shielded_seed0` with the safety mechanism. This shows that the pipeline works; a handful of cases does not measure accuracy. Pilot data, not Directorate data.

## Reading

| Case | Reader | Category | Symptoms | Context | Checks |
|---|---|---|---|---|---|
| results_approval | keyword | no | 4/4 | 2/2 | 10/10 |
| sign_in | keyword | yes | 4/4 | 2/2 | 10/10 |
| fees_release | keyword | yes | 4/4 | 2/2 | 10/10 |
| transcript_duplicates | keyword | no | 4/4 | 2/2 | 10/10 |
| payment_gateway | keyword | yes | 4/4 | 2/2 | 10/10 |
| vague_slow | keyword | yes | 4/4 | 2/2 | 10/10 |
| class_results_slow | keyword | yes | 4/4 | 2/2 | 10/10 |
| profile_cache | keyword | no | 4/4 | 2/2 | 10/10 |

## Reader error rates

Over every check result in every case. Reversed: the logs show a result and the reader records the opposite (the simulator's p_noise). Missed: the logs show a result and the reader records none (p_miss). Invented: the logs show none and the reader records one (not modelled in the simulator). The delegate columns are the delegated check alone.

| Reader | Reversed | Missed | Invented | Delegate reversed | Delegate missed | Delegate invented |
|---|---|---|---|---|---|---|
| keyword | 0/49 (0%) | 0/49 (0%) | 0/31 (0%) | 0/2 (0%) | 0/2 (0%) | 0/6 (0%) |

## Decision

Columns: the agent's decision from each reader's form, and from the expected form. Checks run and blocked proposals in brackets.

| Case | Intended | keyword | expected |
|---|---|---|---|
| results_approval | C02 | fix C02 (verified) (3 checks, 2 blocked) | fix C02 (verified) (3 checks, 2 blocked) |
| sign_in | C08 | fix C08 (verified) (0 checks, 0 blocked) | fix C08 (verified) (0 checks, 0 blocked) |
| fees_release | C06 | escalate (11 checks, 1 blocked) | escalate (11 checks, 1 blocked) |
| transcript_duplicates | C07 | fix C07 (verified) (3 checks, 0 blocked) | fix C07 (verified) (3 checks, 0 blocked) |
| payment_gateway | C01 | escalate (step limit) (9 checks, 6 blocked) | escalate (step limit) (9 checks, 6 blocked) |
| vague_slow | none (escalate) | escalate (step limit), after failed C04 (8 checks, 6 blocked) | escalate (step limit), after failed C04 (8 checks, 6 blocked) |
| class_results_slow | C04 | fix C04 (verified) (6 checks, 5 blocked) | fix C04 (verified) (6 checks, 5 blocked) |
| profile_cache | C05 | fix C05 (verified) (5 checks, 5 blocked) | fix C05 (verified) (5 checks, 5 blocked) |
