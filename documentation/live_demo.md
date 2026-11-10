# Live demo: run sheet

```
run_live_demo.bat
```
(or `python -m streamlit run dashboard/live_app.py --server.port 8502`), then open
http://localhost:8502. This dashboard has only the Live incident and Stress test pages. The full
prototype (`dashboard/prototype_app.py`, port 8501) still has them too, plus the older pages.

Ollama must be running (it starts with Windows; otherwise open "Ollama" from the Start menu) with
`qwen3:4b` pulled. The sidebar shows 🟢 when the local model is ready. Nothing leaves the laptop.

## Order

1. **Live incident → Random hidden fault → New incident.** Point out the 🔒: nobody has seen the
   cause. The ticket and log are written fresh every time (press it twice to show).
   **▶ Let the agent work.** Narrate the console: what it checks, whether the log answers it or
   it probes the system, the belief bars moving, any rule block (⛔), and each fix being applied
   and verified (staging tests for code faults, re-measuring otherwise).
   **🔓 Reveal.** Hidden fault, the outcome, which check results were reversed (noise), and the
   reader's mistakes.
2. **Someone plants the fault.** An audience member picks a cause and presses Plant. The choice
   clears from the screen.
3. **Your own ticket.** Someone dictates a ticket in their own words. The local model reads it
   (about 30–45 s). The hidden system takes the symptoms it found, and the agent investigates.
4. **Stress test → 200 incidents → Run.** It takes seconds: resolved %, first fix %, escalations,
   and how many escalations were sound (even every check would point to the wrong cause).

Playback speed is in the sidebar (about 1.2 s per step reads well).

## Say this honestly

- The live incidents are drawn from the agent's own scenario model (the pilot developer's ratings),
  so they show the pipeline on incidents nobody wrote, not that the model fits Directorate data.
- The local model reads the ticket. Fixed patterns read the log's numbers against thresholds,
  because small models get those wrong: in testing, qwen3:4b reading whole logs took ~2 min and
  called values below a threshold positive.
- The delegate (D11) defaults to the pattern stand-in; the local model is selectable but slow
  (~60 s) and misjudged a library stack trace in testing.

## If something fails

- Sidebar shows ⚪: Ollama is not running, or the model is missing (`ollama pull qwen3:4b`). Live
  random and planted incidents, and the stress test, still work with the keyword reader.
- The old pages (Triage a ticket, All example cases) are unchanged.
