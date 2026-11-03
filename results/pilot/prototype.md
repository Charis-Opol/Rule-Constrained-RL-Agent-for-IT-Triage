# Prototype check (Phase 7)

Six fictional cases written by the researcher (`prototype/examples`), agent `results/pilot/runs/phase5_shielded_seed0` with the safety mechanism. This shows that the pipeline works; six cases do not measure accuracy. Pilot data, not Directorate data.

## Reading

| Case | Reader | Category | Symptoms | Context | Checks |
|---|---|---|---|---|---|
| results_approval | keyword | no | 4/4 | 2/2 | 10/10 |
| sign_in | keyword | yes | 4/4 | 2/2 | 10/10 |
| fees_release | keyword | yes | 4/4 | 2/2 | 10/10 |
| transcript_duplicates | keyword | no | 4/4 | 2/2 | 10/10 |
| payment_gateway | keyword | yes | 4/4 | 2/2 | 10/10 |
| vague_slow | keyword | yes | 4/4 | 2/2 | 10/10 |

## Decision

Columns: the agent's decision from each reader's form, and from the researcher's expected form. Checks run and blocked proposals in brackets.

| Case | Intended | keyword | expected |
|---|---|---|---|
| results_approval | C02 | escalate (forced) (2 checks, 3 blocked) | escalate (forced) (2 checks, 3 blocked) |
| sign_in | C08 | recommend C08 (0 checks, 0 blocked) | recommend C08 (0 checks, 0 blocked) |
| fees_release | C06 | recommend C07 (5 checks, 3 blocked) | recommend C07 (5 checks, 3 blocked) |
| transcript_duplicates | C07 | recommend C07 (2 checks, 2 blocked) | recommend C07 (2 checks, 2 blocked) |
| payment_gateway | C01 | recommend C01 (5 checks, 3 blocked) | recommend C01 (5 checks, 3 blocked) |
| vague_slow | none (escalate) | recommend C04 (5 checks, 4 blocked) | recommend C04 (5 checks, 4 blocked) |
