# Phase 9 log: from "recommend" to "fix", and fix with verification

Started 9 Nov 2026. One entry per step, newest last. Part A is the wording change; Part B is the
model change (fix, then verify). The pilot plan gets a Phase 9 section once both are done.

## Decisions (user, 9 Nov 2026)

- The project's wording changes from "recommend" to "fix" / "act", in the thesis, the prototype
  and the training.
- Do both A (wording only) and B (fix as a real step in training, with verification), then
  retrain. Part A is handed over so training can continue in a different chat.
- The filled Part 2 workbook has come back from the pilot developer (the same developer as Part 1;
  not the Directorate elicitation).

## Entries

### 1. Part 2 workbook received and filed
- `research/elicitation/Pilot_Elicitation_Workbook_Part2_filled.xlsx` copied to
  `research/elicitation/private/Part 2 Responses.xlsx` (git-ignored, like Part 1).
- The filled file in `research/elicitation/` and `prototype/examples/developer/` added to
  `.gitignore`. Reason: several sample tickets carry what look like real endpoint paths, Java class
  names and line numbers, although the workbook asked for invented ones. Check with the developer
  before any of the tickets are quoted in the thesis.
- Contents: code-fix flag and owner role for all 8 causes (fallback: Senior developer); D11 ratings
  for all 8 causes; 20 sample tickets (T01-T20), one of them (T20) with "None of these" as its cause.
- What Part 2 does **not** contain: anything for Part B (harm of a wrong fix, time to roll back,
  whether a remedy can be undone, whether symptoms clear after a fix). Those stay
  researcher-provisional until a Part 3 is filled in.

### 2. Model v2 rebuilt from Part 2
- `python -m experiments.pilot.build_model_v2 --workbook "research/elicitation/private/Part 2 Responses.xlsx"`
  rewrote `pilot_model_v2.json` (source now "pilot developer (Part 2)") and wrote the 20 tickets to
  `prototype/examples/developer/`. `pilot_settings_v2.json` unchanged (max_steps 13).
- Compared with the provisional values: code-fix flags identical (C01, C04, C05, C08). Owners:
  C01 Integrations developer, C04/C05 Backend lead, C06 Release manager (others unchanged).
  D11 P(positive | cause) went from [.75 .25 .25 .75 .75 .75 .50 .50] to
  [.25 .75 .25 .50 .75 .75 .95 .75] for C01-C08.
- `tests/test_extension.py` and `tests/test_prototype.py`: 55 passed on the new model.
- The trained v2 agents (`results/pilot/runs/v2_shielded_seed0-2`) were trained on the provisional
  D11 ratings, so they are out of date. Not deleted; retraining goes to new run folders.

### 3. Part A: wording, code
- Environment, baselines and exact solver: comments and names only (`recommend` -> `fix`). No
  numbers changed.
- Prototype: decision outcome `"recommended"` -> `"fix"` (key `"fix"` holds the cause index);
  CLI prints `FIX:`; the action for a non-code cause is now `fix_order` (was `notice`); messages say
  "Fix:" and "fix decision". Dashboard title "Investigate, Fix or Escalate". Tests updated to match.
- The reader's language-model prompt (`llm.py`) still tells the model not to "recommend an action":
  that is the reader's instruction, not the agent's wording, so it stays.

### 4. Part A: wording, documents
- README: title, the three choices, objective, RQ2, and the data-and-ethics paragraph (which still
  said the prototype "only recommends", out of date since Phase 8).
- Thesis (title, Chapters 1-3): every use that describes this study's agent. Kept as they are: the
  uses that describe cited work (Zhang et al. "solution recommendation", Remil et al. "recommend a
  responsible team") and "recommended practice" (Agarwal et al.). Chapter 1 now says the study takes
  the step "from recommending to acting" that Zhang et al. call least settled, and the scope says
  fixes are applied in simulation and, in the prototype, only to a fictional repository as draft
  changes a person reviews. H2 is now "rule-compliant correct fixes"; the metric is "wrong-fix rate".
- Figure 1.1: "recommend action," replaced by "apply fix," in the PNG (no source file exists; the
  original is kept as `research/archive/Figure_1_1_Conceptual_Framework_recommend.png`).
- Thesis compiles with Tectonic.
- Pilot plan: new Phase 9 section. Earlier phases keep their wording as a record.
- Full test suite after the rewording: 181 passed (3 min 38 s). That run started before the Part B
  edits in entry 5, so re-run it once B is finished.

### 5. Part B: started, NOT finished (opt-in, default off)
- `experiments/pilot/pilot_settings_v3.json`: v2 settings + `fix_with_verification` block
  (researcher-provisional apply minutes and harm weights per remedy, max_failed_fixes 2,
  max_steps 15). Mean harm of a wrong fix = (wrong_fix_multiple - 1) x escalation, so wrong fix +
  escalation costs the elicited 5x on average; the weights follow rule reasons R01-R05.
- `src/sim/scenario.py`: Scenario gets verify, fix_costs, wrong_fix_harm, max_failed_fixes, read by
  `_verification()`; off unless the settings enable it.
- `src/sim/triage_env.py`: with verify on, a correct fix ends the episode with r_correct - apply
  cost; a wrong fix costs apply + harm, sets a "failed" flag (appended to the observation, one per
  cause) and masks that fix; at max_failed_fixes the episode ends as outcome `fix_limit` with the
  escalation cost added. `Layout.failed_fixes(obs)` reads the flags; info has `wrong_fixes`.
  Untested so far.

### 6. Part B: finished (code, tests, documents)
- `src/evaluation.py`: `fix_limit` counts as an escalation; new `wrong_fix_rate` and
  `mean_wrong_fixes` (equal to `wrong_rate` when verification is off).
- `src/agents/belief.py` / `baselines.py`: the posterior rules out causes whose fix failed.
- `src/agents/exact.py` refuses verification mode; `train_dqn.py` and `dashboard/thinking.py`
  skip the exact reference in that mode.
- `src/prototype/triage.py`: bug fixed (the live environment's reset did not set the new
  `failed` flags, so the prototype would have crashed); it refuses v3 settings until it has a
  verification step.
- `tests/test_verify.py`: 11 tests, all pass. One first failed because the test was wrong: a fix the
  safety mechanism *blocked* was never applied, so it may be proposed again; the test now checks
  only applied-and-failed fixes.
- Baselines on v2 vs v3 (table in the pilot plan, Phase 9): Threshold resolves 75% with
  verification against 62% without, but its return falls (-0.61 against -0.29) because wrong
  remedies now do harm.
- Chapter 3: new subsection "Fix with Verification". Pilot plan: Phase 9 Part B written up, with
  the v3 training command.
- Full test suite after Part B: 192 passed (about 10 min, on a loaded machine). Thesis compiles.
- Not done: training v3 (for the training chat, after the v2 retrain); a Part 3 workbook for the
  provisional remedy values; a verification step in the prototype.
