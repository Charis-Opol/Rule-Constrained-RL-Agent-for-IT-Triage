"""Live demo dashboard: hidden-fault incidents and the stress test, on their own port.

    python -m streamlit run dashboard/live_app.py --server.port 8502   (or: run_live_demo.bat)

A fault is drawn from the scenario model and kept hidden; the ticket and monitoring log are written
fresh from it; the trained agent reads them, probes, fixes and verifies; then the fault is revealed.
Separate from the full prototype (dashboard/prototype_app.py, port 8501) so both can run at once.
Messages go to the outbox folder and are never sent; pull requests are drafts.
"""
import json
import os
import secrets
import subprocess
import sys
import time
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.agents.dqn import MaskedDQN                                      # noqa: E402
from src.prototype.cli import load_inputs, make_reader                    # noqa: E402
from src.prototype.delegate import make_delegate                          # noqa: E402
from src.prototype import live                                            # noqa: E402
from src.prototype.local_llm import status as llm_status                # noqa: E402
from src.prototype.reading import NOT_SHOWN                         # noqa: E402
from src.prototype.triage import run_settings                 # noqa: E402

RUNS = ROOT / "results" / "pilot" / "runs"
GREEN, RED, GREY, BLUE = "#2e7d32", "#c62828", "#757575", "#2a78d6"

st.set_page_config(page_title="Live Incident Demo", layout="wide")

# ----- Data ------------------------------------------------------------------
@st.cache_resource
def inputs(settings_path=None):
    return load_inputs(settings_path=settings_path)


@st.cache_resource
def load_agent(path):
    return MaskedDQN.load(path, device="cpu")


def usable_runs(config):
    """Finished runs on the prototype's model at the elicited escalation cost."""
    out = []
    want = Path(config["model"]).as_posix()
    for run in sorted(RUNS.iterdir()) if RUNS.exists() else []:
        cfg_path = run / "config.json"
        if not (cfg_path.exists() and (run / "final.zip").exists()):
            continue
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        if Path(cfg["model"]).as_posix() == want and cfg.get("escalation_minutes") in (None, 120.0):
            out.append(run.relative_to(ROOT).as_posix())
    return out

def has_key():
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


@st.cache_data(ttl=20, show_spinner=False)
def local_llm():
    return llm_status()

# ----- Sidebar ---------------------------------------------------------------
model, config, _ = inputs()
names = {x["id"]: x["name"] for group in ("symptoms", "context", "checks") for x in model[group]}
check_by_id = {c["id"]: c for c in model["checks"]}

with st.sidebar:
    st.header("Set-up")
    runs = usable_runs(config)
    default = config["agent_run"] if config["agent_run"] in runs else (runs[0] if runs else None)
    if not runs:
        st.error("No trained agent for this model. Train one with experiments.pilot.train_dqn.")
        st.stop()
    run = st.selectbox("Agent", runs, index=runs.index(default), format_func=lambda r: Path(r).name,
                       help="Agents trained on the prototype's model. v3 agents verify every fix.")
    model, config, scenario = inputs(str(run_settings(ROOT / run, ROOT / config["settings"])))
    st.caption("v3 agents verify every fix against the hidden system." if scenario.verify else
               "This agent was trained without verification: a fix ends the incident.")
    key = has_key()
    llm_ok, llm_msg = local_llm()
    llm_names = (["local"] if llm_ok else []) + (["claude"] if key else [])
    reader_name = st.radio("Reader", ["keyword"] + llm_names, horizontal=True,
                           help="keyword: offline patterns, instant. local: a free open model on this laptop "
                                "(Ollama), nothing leaves the machine, slower. claude: the Claude API.")
    delegate_name = st.radio("Delegate (D11)", ["pattern"] + llm_names + ["off"], horizontal=True,
                             help="Who answers a delegated full log analysis.")
    st.caption(("🟢 " if llm_ok else "⚪ ") + f"Local model: {llm_msg}"
               + ("" if key else "  \nNo ANTHROPIC_API_KEY: Claude options off."))
    speed = st.slider("Playback: seconds per step", 0.0, 3.0, 1.2, 0.1, help="Live incident page only.")
    st.divider()
    act_on = st.toggle("Carry the decision out", value=True,
                       help="Draft pull request on the toy repository, fix order or escalation message.")
    pr_mode = st.radio("Pull requests", ["local", "off"], horizontal=True, disabled=not act_on,
                       help="local: a draft branch in results/pilot/demo_repo.")
    patcher = st.radio("Patch writer", ["pre-written", "claude"], horizontal=True,
                       disabled=not (act_on and key), index=0)
    st.divider()
    st.caption(f"Model: `{config['model']}`  \nSettings: `{config['settings']}`  \nPilot data (one developer's "
               "ratings), not Directorate data. Fictional or approved tickets only.")


# ----- Rendering helpers -----------------------------------------------------
def reading_table(reading):
    rows = [{"Item": f"{k} {names[k]}", "Value": f["value"], "Evidence": f.get("evidence") or ""}
            for group in ("symptoms", "context") for k, f in reading[group].items()]
    rows += [{"Item": f"{k} {names[k]}", "Value": f["value"], "Evidence": f.get("evidence") or ""}
             for k, f in reading["checks"].items() if f["value"] != NOT_SHOWN]
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")


def decision_card(report):
    d = report["decision"]
    if d["outcome"] in ("fix", "awaiting_verification"):
        ok = "re-confirmed by the rule checker" if d.get("permitted") else "NOT confirmed by the rule checker"
        verified = ""
        if d.get("verified"):
            last = d["attempts"][-1]
            verified = f"  \nVerified ({last['how']}): {last['detail']}."
        text = f"**Fix:** {d['remedy']}  \nLikely cause {d['cause']}: {d['cause_name']} ({ok}).{verified}"
        (st.success if d["outcome"] == "fix" else st.info)(text)
    else:
        st.warning(f"**Escalate to a person.** {d['reason']}")
    for warning in report.get("warnings", []):
        st.warning(warning)


def action_card(action):
    st.markdown(f"**{action['kind'].replace('_', ' ').capitalize()}** → {action['owner']}  \n"
                f"<span style='color:{GREY}'>Routed because {action['routed_because']}</span>",
                unsafe_allow_html=True)
    if "pull_request" in action:
        pr = action["pull_request"]
        st.info(f"Draft pull request `{pr['branch']}`: {pr['where']}  \nPatch `{pr['patch']}` by {pr['patch_source']}; "
                f"tests: {pr['tests']}")
        diff = repo_diff(pr["branch"])
        if diff:
            with st.expander("Patch (diff against main)"):
                st.code(diff, language="diff")
        with st.expander("Pull request description"):
            st.markdown(pr["body"])
    if "refused" in action:
        st.error(f"No pull request: {action['refused']}")
    message = Path(action["message"])
    if message.exists():
        with st.expander(f"Message to {action['owner']} (simulated, not sent)"):
            st.markdown(message.read_text(encoding="utf-8"))


def repo_diff(branch):
    repo = ROOT / config["actions"]["local_repo"]
    if not (repo / ".git").exists():
        return ""
    out = subprocess.run(["git", "diff", f"main...{branch}"], cwd=repo, capture_output=True, text=True)
    return out.stdout if out.returncode == 0 else ""


def carry_out(report, incident, ticket):
    from src.prototype.actions import act
    return act(report, model, config["actions"], incident, ticket, pr=pr_mode, patcher=patcher)


# ----- Live incident ---------------------------------------------------------
CAUSES = {c["id"]: c for c in model["causes"]}
SETTINGS = json.loads(Path(run_settings(ROOT / run, ROOT / config["settings"])).read_text(encoding="utf-8"))
CHECK_MINUTES = {c["id"]: SETTINGS["check_minutes"][c["effort"]] for c in model["checks"]}
SOURCE = {"logs": "read from the log", "ticket": "read from the ticket", "probe": "probed live on the system",
          "operator": "answered by the operator", "delegate (logs)": "delegated analysis of the log",
          "delegate (ticket)": "delegated analysis of the ticket", "delegate": "delegated analysis"}
CODE_CSS = """<style>
.step {border-left: 4px solid var(--c); padding: 6px 12px; margin: 6px 0; border-radius: 4px;
       background: color-mix(in srgb, var(--c) 7%, transparent);}
.step .alt {color: #888; font-size: 0.82em;}
.ticket {border: 1px solid #8884; border-radius: 8px; padding: 12px 16px; white-space: pre-wrap;}
</style>"""


def cause_label(cid):
    return f"{cid} {CAUSES[cid]['name']}"


def belief_bars(slot, belief, title, hidden=None):
    df = pd.DataFrame([{"Cause": cause_label(c["id"]), "Probability": p,
                        "Hidden": "hidden fault" if c["id"] == hidden else "other"}
                       for c, p in zip(model["causes"], belief)])
    colour = (alt.Color("Hidden:N", scale=alt.Scale(domain=["hidden fault", "other"], range=[GREEN, BLUE]),
                        legend=None) if hidden else alt.value(BLUE))
    chart = alt.Chart(df, title=title).mark_bar(cornerRadiusEnd=3).encode(
        x=alt.X("Probability:Q", axis=alt.Axis(format="%"), scale=alt.Scale(domain=[0, 1]), title=None),
        y=alt.Y("Cause:N", sort=None, title=None, axis=alt.Axis(labelLimit=260)),
        color=colour, tooltip=["Cause", alt.Tooltip("Probability:Q", format=".0%")]).properties(height=300)
    slot.altair_chart(chart, width="stretch")


def step_html(i, s):
    alts = " · ".join(f"{a['action'].split(':')[0]} {a['value']:.2f}" for a in s.get("alternatives", []))
    head = f"<b>Step {i} · {s['action']}</b>"
    if "blocked_by" in s:
        why = "; ".join(f"rule {b['rule']} (needs {b['needs'] or 'a person'}): {b['reason']}" for b in s["blocked_by"])
        return RED, f"{head}<br>⛔ Blocked by the safety mechanism: {why}. The agent must choose again."
    if "verification" in s:
        v = s["verification"]
        mark = {True: "✅ Symptoms cleared", False: "❌ Symptoms persist", None: "⏳ Waiting for verification"}[v["cleared"]]
        colour = GREEN if v["cleared"] else RED if v["cleared"] is False else BLUE
        return colour, f"{head}<br>🔧 Remedy applied, then verified ({v['how']}).<br>{mark}: {v['detail']}"
    if s["action"].startswith("Run"):
        cid = s["action"].split()[1]
        result = s.get("result", "")
        colour = GREEN if result == "positive" else GREY if result == "negative" else RED
        where = SOURCE.get(s.get("source", ""), s.get("source", ""))
        ev = (s.get("evidence") or "").replace("<", "&lt;")
        extra = f"Delegate's report: {s['delegation']['report']}<br>" if s.get("delegation") else ""
        return colour, (f"{head} <span class='alt'>({CHECK_MINUTES[cid]} min)</span><br>"
                        f"Result: <b>{result}</b>, {where}<pre style='margin:4px 0;white-space:pre-wrap'>{ev}</pre>"
                        f"{extra}<span class='alt'>Agent's values: {alts}</span>")
    if s["action"].startswith("Escalate"):
        return GREY, f"{head}<br>🙋 Hands the incident to a person.<br><span class='alt'>Agent's values: {alts}</span>"
    return BLUE, f"{head}<br><span class='alt'>Agent's values: {alts}</span>"


def console(report, animate, hidden=None):
    left, right = st.columns([3, 2])
    with right:
        slot = st.empty()
        st.caption("Reference belief, worked out from the ratings for the people watching. The agent never sees it; "
                   "it acts on its own learned values (shown under each step).")
    belief_bars(slot, report["start_belief"], "Before any check: from the symptoms alone", hidden)
    with left:
        st.markdown("#### The agent's console")
        for i, s in enumerate(report["steps"], 1):
            if animate:
                wait = st.empty()
                wait.caption(f"Step {i}: choosing…")
                time.sleep(speed * 0.5)
                wait.empty()
            colour, html = step_html(i, s)
            st.markdown(f"<div class='step' style='--c:{colour}'>{html}</div>", unsafe_allow_html=True)
            if animate:
                belief_bars(slot, s["belief"], f"After step {i}", hidden)
                time.sleep(speed)
    if not animate:
        belief_bars(slot, report["steps"][-1]["belief"], f"After step {len(report['steps'])}", hidden)


def reveal(report, incident, reading):
    d = report["decision"]
    hidden = incident.cause
    best, p = live.hindsight(incident, model, scenario)
    result = live.outcome(report, incident)
    c1, c2, c3 = st.columns(3)
    c1.metric("Hidden fault", hidden, help=CAUSES[hidden]["name"])
    c2.metric("Agent", d["cause"] if d["outcome"] == "fix" else "escalated")
    c3.metric("Outcome", result)
    st.markdown(f"**The hidden fault was {cause_label(hidden)}.** Remedy: {CAUSES[hidden]['remedy']}.")
    if result.startswith("resolved"):
        st.success("The agent found it" + (" after a fix that did not work." if "failed" in result else " first time."))
    elif best != hidden:
        st.info(f"The agent escalated. With every check run, the evidence would point to {cause_label(best)} "
                f"({p:.0%}), not the hidden fault: the evidence itself misleads here, so handing over is sound.")
    else:
        st.warning(f"The agent escalated. With every check run, the evidence would point to the hidden fault "
                   f"({p:.0%}), so this escalation was cautious: it cost a person's time, but did no harm.")
    rev = incident.reversed
    st.markdown("**Reversed check results** (each check reports wrongly 10% of the time, as in training): "
                + (", ".join(f"{k} {names[k]}" for k in rev) if rev else "none in this incident"))
    errs = live.reading_errors(reading, incident, model)
    st.markdown(f"**Reader's mistakes** ({report['reading']['reader']}): " + ("; ".join(errs) if errs else "none"))
    t = report.get("timing", {})
    st.caption(f"Reading took {t.get('read_seconds', 0)} s, deciding {t.get('decide_seconds', 0)} s. "
               f"Incident #{incident.seed} ({incident.origin}).")


def live_page():
    state = st.session_state
    st.markdown(CODE_CSS, unsafe_allow_html=True)
    st.caption("A fault is drawn from the scenario model and kept hidden, from the presenter too. The ticket and the "
               "monitoring log are written fresh from it, with background noise, near misses and, like real checks, "
               "results that are sometimes wrong. The agent reads them, probes the system for anything the log does "
               "not show, and applies and verifies fixes against the hidden fault. Then it is revealed.")
    mode = st.radio("Where the incident comes from", ["Random hidden fault", "Someone plants the fault",
                                                      "Your own ticket"], horizontal=True)
    if mode == "Random hidden fault":
        if st.button("New incident", type="primary"):
            state.live = {"incident": live.draw(model, scenario, secrets.randbelow(10**6))}
    elif mode == "Someone plants the fault":
        options = ["(choose, then press Plant)"] + list(CAUSES)

        def plant():
            pick = state.get("plant_pick")
            if pick in CAUSES:
                state.live = {"incident": live.draw(model, scenario, secrets.randbelow(10**6), cause=pick)}
            state.plant_pick = options[0]          # clear the choice from the screen
        c1, c2 = st.columns([3, 1])
        c1.selectbox("Fault to plant (let a member of the audience choose)", options, key="plant_pick",
                     format_func=lambda c: c if c not in CAUSES else cause_label(c))
        c2.button("Plant it", type="primary", on_click=plant)
    else:
        own = st.text_area("Write a ticket as a user would", height=110, key="own_ticket",
                           placeholder="e.g. Since this morning students get an error page when they open their "
                                       "results, and it is very slow. This is the live portal, it is urgent.")
        own_reader = st.radio("Read by", llm_names + ["keyword"], horizontal=True, key="own_reader",
                              help="local: the free open model on this laptop, about 30-40 s. keyword: instant, but "
                                   "only knows its keyword lists.")
        st.caption("The hidden system takes the symptoms, context and any check results the reader finds in your "
                   "ticket, and a cause is drawn given them. Then the agent investigates it like any other incident.")
        if st.button("Read it and hide a matching fault", type="primary") and own.strip():
            try:
                t0 = time.perf_counter()
                with st.spinner(f"Reading with {own_reader}… (the local model takes about half a minute)"):
                    reading = make_reader(own_reader, model, config).read(own, "")
                incident = live.from_ticket(reading, own, model, scenario, secrets.randbelow(10**6))
                state.live = {"incident": incident, "reading": reading,
                              "read_seconds": round(time.perf_counter() - t0, 1)}
            except Exception as error:
                st.error(f"{type(error).__name__}: {error}")

    job = state.get("live")
    if not job:
        return
    incident = job["incident"]
    st.divider()
    h1, h2 = st.columns([4, 1])
    h1.markdown(f"### Incident #{incident.seed}")
    lock = "🔒 fault hidden" if not job.get("revealed") else f"🔓 {incident.cause}"
    h2.markdown(f"<div style='text-align:right;padding-top:14px'>{lock}</div>", unsafe_allow_html=True)
    t1, t2 = st.columns([2, 3])
    with t1:
        st.markdown("**Ticket**")
        st.markdown(f"<div class='ticket'>{incident.ticket.replace('<', '&lt;')}</div>", unsafe_allow_html=True)
    with t2:
        st.markdown(f"**Monitoring log** ({len(incident.logs.splitlines())} lines)")
        st.code(incident.logs, language=None, height=260)

    if "report" not in job:
        if not st.button("▶ Let the agent work", type="primary"):
            return
        try:
            with st.spinner(f"Reading the ticket and log with {reader_name}…"):
                delegate = None if delegate_name == "off" else make_delegate(delegate_name, config)
                reader = make_reader(reader_name, model, config)
                reading, report = live.run(incident, reader, scenario, model, load_agent(str(ROOT / run / "final.zip")),
                                           config, delegate=delegate, staging=True, patcher=patcher,
                                           reading=job.get("reading"), read_seconds=job.get("read_seconds", 0))
            job.update(report=report, reading=reading, animate=True)
        except Exception as error:
            st.error(f"{type(error).__name__}: {error}")
            return
    report = job["report"]
    with st.expander(f"What the reader found ({report['reading']['reader']})"):
        reading_table(report["reading"])
    console(report, job.pop("animate", False), incident.cause if job.get("revealed") else None)
    st.markdown("#### Decision")
    decision_card(report)
    if not job.get("revealed"):
        if st.button("🔓 Reveal the hidden fault", type="primary"):
            job["revealed"] = True
            st.rerun()
    else:
        reveal(report, incident, job["reading"])
    if act_on:
        with st.expander("Carry the decision out (draft pull request, fix order or escalation, all simulated)"):
            if job.get("action") is None and st.button("Carry it out"):
                try:
                    job["action"] = carry_out(report, f"live-{incident.seed}", incident.ticket)
                except Exception as error:
                    st.error(f"{type(error).__name__}: {error}")
            if job.get("action"):
                action_card(job["action"])


def stress_page():
    st.caption("Many fresh incidents, each with a hidden fault, through the same reader, agent and safety mechanism, "
               "with nothing written by hand. Uses the keyword reader and pattern delegate (instant); fixes are "
               "verified by re-measuring the hidden system (no staging tests, for speed). The seeds are new every run.")
    c1, c2 = st.columns([3, 1])
    n = c1.slider("Incidents", 20, 500, 100, 10)
    if not c2.button("Run", type="primary"):
        return
    first = secrets.randbelow(10**6)
    reader, delegate = make_reader("keyword", model, config), make_delegate("pattern", config)
    agent = load_agent(str(ROOT / run / "final.zip"))
    rows, bar = [], st.progress(0.0)
    tiles = st.empty()
    for k in range(n):
        incident = live.draw(model, scenario, first + k)
        reading, report = live.run(incident, reader, scenario, model, agent, config, delegate=delegate, staging=False)
        d = report["decision"]
        best, _ = live.hindsight(incident, model, scenario)
        rows.append({"Incident": incident.seed, "Hidden fault": incident.cause, "Outcome": live.outcome(report, incident),
                     "Agent": d["cause"] if d["outcome"] == "fix" else "escalated",
                     "Evidence points to": best, "Checks": d["checks_run"], "Check minutes": d["check_minutes"],
                     "Failed fixes": sum(a["cleared"] is False for a in d.get("attempts", [])),
                     "Blocked": d["blocked_proposals"], "Reversed results": len(incident.reversed)})
        if (k + 1) % 10 == 0 or k + 1 == n:
            bar.progress((k + 1) / n)
            df = pd.DataFrame(rows)
            resolved = df["Outcome"].str.startswith("resolved")
            sound = ~resolved & (df["Evidence points to"] != df["Hidden fault"])
            with tiles.container():
                m = st.columns(5)
                m[0].metric("Incidents", len(df))
                m[1].metric("Resolved", f"{resolved.mean():.0%}", help="The fix cleared the symptoms.")
                m[2].metric("First fix worked", f"{(df['Outcome'] == 'resolved').mean():.0%}")
                m[3].metric("Escalated", f"{(~resolved).mean():.0%}",
                            help=f"Of which {int(sound.sum())} where even every check would point to the wrong cause.")
                m[4].metric("Mean check time", f"{df['Check minutes'].mean():.0f} min")
    df = pd.DataFrame(rows)
    order = ["resolved", "resolved after a failed fix", "escalated", "escalated after failed fixes"]
    chart = alt.Chart(df).mark_bar().encode(
        y=alt.Y("Hidden fault:N", title=None), x=alt.X("count():Q", title="Incidents"),
        color=alt.Color("Outcome:N", scale=alt.Scale(domain=order, range=[GREEN, "#81c784", GREY, RED])),
        order=alt.Order("Outcome:N")).properties(height=280, title="Outcome by hidden fault")
    st.altair_chart(chart, width="stretch")
    esc = df[~df["Outcome"].str.startswith("resolved")]
    st.caption(f"Of {len(esc)} escalations, {int((esc['Evidence points to'] != esc['Hidden fault']).sum())} were "
               "incidents where every check together would still point to the wrong cause (reversed results or "
               "overlap), so a fix would likely have failed. Every fix is verified, so none 'succeeds' wrongly.")
    with st.expander("Every incident"):
        st.dataframe(df, hide_index=True, width="stretch")

# ----- Layout ----------------------------------------------------------------
st.title("Live Incident Demo")
st.caption(f"Live demo build · agent `{Path(run).name}` · reader `{reader_name}` · delegate `{delegate_name}`")
tabs = st.tabs(["Live incident", "Stress test"])
with tabs[0]:
    live_page()
with tabs[1]:
    stress_page()
