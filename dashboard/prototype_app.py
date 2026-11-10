"""Prototype dashboard: the agent as a decision layer, end to end.

    streamlit run dashboard/prototype_app.py

Ticket and logs -> reader -> trained agent (with the safety mechanism) -> action: a draft pull
request on the fictional toy repository, a fix order, or an escalation routed to an owner.
Separate from the training dashboard (dashboard/app.py). Pilot model: use fictional or approved
tickets only. Messages go to the outbox folder and are never sent; pull requests are drafts.

Agents trained with fix-with-verification settings (v3) have every fix verified before they go
on: a code fault on a staging copy of the toy repository against the case's reproduction tests,
otherwise by asking you whether the symptoms cleared (or, for the example cases, from the cause
the case was written to show). Verifying acts on nothing real, so the incident is simply replayed
with each new answer; the decision is carried out only when you press "Carry it out".
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
from src.prototype.local_llm import LocalLLM, status as llm_status       # noqa: E402
from src.prototype.reading import NEGATIVE, NOT_SHOWN, POSITIVE, Finding  # noqa: E402
from src.prototype.triage import run_settings, triage                     # noqa: E402
from src.prototype.verify import make_verifier                            # noqa: E402

EXAMPLES = ROOT / "prototype" / "examples"
RUNS = ROOT / "results" / "pilot" / "runs"
GREEN, RED, GREY, BLUE = "#2e7d32", "#c62828", "#757575", "#2a78d6"

st.set_page_config(page_title="Triage Prototype", layout="wide")


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


def examples():
    return sorted(p.name for p in EXAMPLES.iterdir() if (p / "ticket.txt").exists()) if EXAMPLES.exists() else []


def intended_causes():
    path = EXAMPLES / "cases.json"
    if not path.exists():
        return {}
    cases = json.loads(path.read_text(encoding="utf-8")).get("cases", {})
    return {name: c.get("intended_cause") for name, c in cases.items()}


def text(name, file):
    path = EXAMPLES / name / file
    return path.read_text(encoding="utf-8") if path.exists() else ""


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
    if scenario.verify:
        verify_source = st.radio("Did the fix clear the symptoms?", ["Ask me", "From the case (demo)"],
                                 horizontal=True,
                                 help="Code faults with a reproduction test are always checked on a staging copy "
                                      "of the toy repository. For the rest: ask you, or (example cases only) use "
                                      "the cause the case was written to show.")
    else:
        verify_source = None
        st.caption("This agent was trained without verification: a fix ends the incident.")
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
def pipeline_strip(report, action):
    d = report["decision"]
    blocked = d["blocked_proposals"]
    if d["outcome"] == "fix":
        verdict, colour = f"Fix {d['cause']}" + (" (verified)" if d.get("verified") else ""), GREEN
    elif d["outcome"] == "awaiting_verification":
        verdict, colour = f"Fix {d['cause']}?", BLUE
    else:
        verdict, colour = "Escalate", GREY
    act = "not carried out" if action is None else action["kind"].replace("_", " ")
    stages = [("Reader", report["reading"]["reader"]), ("Agent", f"{d['checks_run']} checks, {d['check_minutes']} min"),
              ("Safety mechanism", f"{blocked} blocked" if blocked else "nothing blocked"),
              ("Decision", verdict), ("Action", act)]
    tried = [a for a in d.get("attempts", []) if a["cleared"] is False]
    if tried:
        stages.insert(3, ("Fixes that failed", ", ".join(a["cause"] for a in tried)))
    cols = st.columns(len(stages))
    for col, (label, value) in zip(cols, stages):
        col.metric(label, value)
    st.markdown(f"<div style='height:4px;background:{colour};border-radius:2px;margin:-6px 0 12px'></div>",
                unsafe_allow_html=True)


def reading_table(reading):
    rows = [{"Item": f"{k} {names[k]}", "Value": f["value"], "Evidence": f.get("evidence") or ""}
            for group in ("symptoms", "context") for k, f in reading[group].items()]
    rows += [{"Item": f"{k} {names[k]}", "Value": f["value"], "Evidence": f.get("evidence") or ""}
             for k, f in reading["checks"].items() if f["value"] != NOT_SHOWN]
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")


def steps_table(report):
    rows = []
    for i, s in enumerate(report["steps"], 1):
        result = s.get("result", "")
        if "blocked_by" in s:
            result = "BLOCKED: " + "; ".join(f"{b['rule']} needs {b['needs']}" for b in s["blocked_by"])
        if "delegation" in s:
            result += f" (delegated: {s['delegation'].get('delegate', '')})"
        if "verification" in s:
            v = s["verification"]
            result = {True: "symptoms cleared", False: "FAILED: symptoms persist",
                      None: "waiting for verification"}[v["cleared"]] + f" ({v['how']})"
        rows.append({"Step": i, "Action": s["action"], "Result": result, "Value": s["value"],
                     "Lead over next": s["margin"], "Escalate value": s["escalate_value"]})
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch",
                 column_config={k: st.column_config.NumberColumn(format="%.2f")
                                for k in ("Value", "Lead over next", "Escalate value")})
    for s in report["steps"]:
        for b in s.get("blocked_by", []):
            st.caption(f"Rule {b['rule']} blocked “{s['action']}”: {b['reason']}")
        if s.get("verification", {}).get("cleared") is not None:
            st.caption(f"Verification of “{s['action']}”: {s['verification']['detail']}")


def belief_chart(report):
    df = pd.DataFrame([{"Cause": f"{r['cause']} {r['name']}", "Probability": r["probability"]}
                       for r in report["reference"]])
    chart = alt.Chart(df).mark_bar(color=BLUE, cornerRadiusEnd=3).encode(
        x=alt.X("Probability:Q", axis=alt.Axis(format="%"), scale=alt.Scale(domain=[0, 1])),
        y=alt.Y("Cause:N", sort="-x", title=None),
        tooltip=["Cause", alt.Tooltip("Probability:Q", format=".0%")]).properties(height=34 * len(df) + 20)
    st.altair_chart(chart, width="stretch")
    st.caption("Calculated from the ratings for the person who takes it next. The agent does not see this.")


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


def run_triage(ticket, logs, answers, incident, verify_answers=None, demo=False):
    reading = make_reader(reader_name, model, config).read(ticket, logs)
    delegate = None if delegate_name == "off" else make_delegate(delegate_name, config)

    def ask(check):
        value = answers.get(check["id"])
        return Finding(value, "reported by the operator", "operator") if value in (POSITIVE, NEGATIVE) else None

    verify = None
    if scenario.verify:
        case_dir = EXAMPLES / incident if (EXAMPLES / incident).is_dir() else None
        verify = make_verifier(config["actions"], case_dir, patcher, answers=verify_answers,
                               intended=intended_causes().get(incident), demo=demo)
    return triage(reading, scenario, model, load_agent(str(ROOT / run / "final.zip")), ask=ask if answers else None,
                  delegate=delegate, ticket=ticket, logs=logs, verify=verify)


def carry_out(report, incident, ticket):
    from src.prototype.actions import act
    return act(report, model, config["actions"], incident, ticket, pr=pr_mode, patcher=patcher)


# ----- Pages -----------------------------------------------------------------
def triage_page():
    st.caption("Paste a ticket and its logs, or start from an example. The reader turns them into symptoms, context "
               "and check results; the agent decides what to check, then fixes or escalates; the safety mechanism "
               "checks every proposal. Fixes become draft pull requests or fix orders that a person approves.")
    c1, c2 = st.columns([2, 1])
    choice = c1.selectbox("Example", ["(none)"] + examples())
    name = "" if choice == "(none)" else choice
    intended = intended_causes().get(name)
    if intended:
        c2.metric("Written to show", intended, help="The cause the case was written for; not ground truth.")
    ticket = st.text_area("Ticket", text(name, "ticket.txt"), height=120, key=f"t{name}")
    logs = st.text_area("Logs", text(name, "logs.txt"), height=180, key=f"l{name}")
    answers = {}
    with st.expander("Answer checks the logs do not show (optional, as the operator)"):
        st.caption("Without an answer such a check is unavailable to the agent. Delegated checks go to the delegate.")
        cols = st.columns(3)
        for i, c in enumerate(x for x in model["checks"] if not x.get("delegated")):
            value = cols[i % 3].selectbox(f"{c['id']} {c['name']}", ["(not given)", POSITIVE, NEGATIVE],
                                          key=f"a{name}{c['id']}", help=f"Positive means: {c['positive_means']}")
            if value != "(not given)":
                answers[c["id"]] = value
    signature = json.dumps([run, name, ticket, logs, answers, reader_name, delegate_name, patcher, verify_source])
    state = st.session_state
    if st.button("Triage", type="primary") and ticket.strip():
        state.job, state.verify_answers, state.action = signature, {}, None
    if state.get("job") != signature:
        if state.get("job"):
            st.caption("The inputs changed: press Triage again.")
        return
    incident = name or "pasted"
    try:
        with st.spinner("Reading and deciding..."):
            report = run_triage(ticket, logs, answers, incident, state.verify_answers,
                                demo=verify_source == "From the case (demo)")
    except Exception as error:             # missing credentials, refusal, network
        st.error(f"{type(error).__name__}: {error}")
        return
    action = state.get("action")

    pipeline_strip(report, action)
    left, right = st.columns([1, 1])
    with left:
        st.subheader("1 · Reading")
        st.markdown(f"Category: **{report['reading']['category']}**  \n{report['reading'].get('summary', '')}")
        reading_table(report["reading"])
        for warning in report["reading"].get("warnings", []):
            st.warning(warning)
    with right:
        st.subheader("2 · What the agent did")
        steps_table(report)
        st.subheader("3 · Decision")
        decision_card(report)
        belief_chart(report)
    d = report["decision"]
    if d["outcome"] == "awaiting_verification":
        st.subheader("4 · Verify the fix")
        st.markdown(f"The agent applies **{d['remedy']}** (cause {d['cause']}). Once it has been applied, "
                    "do the symptoms clear?")
        c1, c2, _ = st.columns([1, 1, 3])
        if c1.button("Yes, they cleared", type="primary"):
            state.verify_answers[d["cause"]] = True
            st.rerun()
        if c2.button("No, they persist"):
            state.verify_answers[d["cause"]] = False
            st.rerun()
        st.caption("A failed fix is flagged to the agent, which goes on: more checks, another fix, or escalation. "
                   "Nothing is carried out until the outcome is final.")
    elif act_on:
        st.subheader("4 · Action")
        if action is None:
            if st.button("Carry it out", type="primary",
                         help="Open the draft pull request, or write the fix order or escalation to the outbox."):
                try:
                    state.action = carry_out(report, incident, ticket)
                    st.rerun()
                except Exception as error:   # refused action
                    st.error(f"{type(error).__name__}: {error}")
        if action is not None:
            action_card(action)
    st.download_button("Download the full report (JSON)", json.dumps({**report, "action": action}, indent=2),
                       file_name=f"triage_{name or 'pasted'}.json", mime="application/json")


def cases_page():
    st.caption("Every example case through the reader and the agent, without carrying anything out. With a v3 "
               "agent, code fixes are verified on staging and other fixes from the case (demo only). "
               "'Written to show' is the cause each case was written for, not ground truth; vague_slow was written "
               "to have none, so escalating is the expected answer there.")
    if not st.button("Run all cases", type="primary"):
        return
    intended = intended_causes()
    rows = []
    progress = st.progress(0.0)
    names_ = examples()
    for i, name in enumerate(names_):
        try:
            report = run_triage(text(name, "ticket.txt"), text(name, "logs.txt"), {}, name, demo=True)
            d = report["decision"]
            got = d.get("cause") if d["outcome"] == "fix" else "escalate"
            failed = ", ".join(a["cause"] for a in d.get("attempts", []) if a["cleared"] is False)
            want = intended.get(name) or "escalate"
            rows.append({"Case": name, "Written to show": want, "Decision": got, "Match": got == want,
                         "Fixes that failed": failed,
                         "Checks": d["checks_run"], "Minutes": d["check_minutes"], "Blocked": d["blocked_proposals"],
                         "Top cause (reference)": f"{report['reference'][0]['cause']} "
                                                  f"{report['reference'][0]['probability']:.0%}"})
        except Exception as error:
            rows.append({"Case": name, "Decision": f"error: {error}"})
        progress.progress((i + 1) / len(names_))
    df = pd.DataFrame(rows)
    st.dataframe(df, hide_index=True, width="stretch")
    if "Match" in df:
        st.metric("Matches the case's intended answer", f"{int(df['Match'].sum())} of {len(df)}")


def outbox_page():
    outbox = ROOT / config["actions"]["outbox"]
    files = sorted(outbox.glob("*.md"), reverse=True) if outbox.exists() else []
    left, right = st.columns([1, 2])
    with left:
        st.subheader("Outbox")
        st.caption("Simulated messages: escalations, fix orders and draft pull request notices. Nothing is sent.")
        if not files:
            st.info("Empty. Triage a case with 'Carry the decision out' on.")
            return
        pick = st.radio("Message", files, format_func=lambda p: p.stem, label_visibility="collapsed")
    with right:
        st.markdown(pick.read_text(encoding="utf-8"))
    repo = ROOT / config["actions"]["local_repo"]
    if (repo / ".git").exists():
        st.subheader("Draft branches in the local toy repository")
        out = subprocess.run(["git", "branch", "--list", "triage/*", "--format=%(refname:short)  %(subject)"],
                             cwd=repo, capture_output=True, text=True).stdout.strip()
        st.code(out or "(none)")


def accuracy_page():
    st.caption("How often the readers and the delegate got check results wrong, against the researcher's expected "
               "readings (from experiments.pilot.evaluate_prototype). Reversed results inform p_noise and missed "
               "ones p_miss. Only the pilot developer's sample tickets measure accuracy; the researcher's own cases "
               "do not.")
    for path in sorted((ROOT / "results" / "pilot").glob("prototype*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        st.subheader(path.stem)
        st.caption(f"Agent: `{data.get('agent_run', '?')}` · model: `{data.get('model', '?')}`")
        rows = [{"Reader": reader, "Part": part, **counts}
                for reader, parts in data.get("errors", {}).items() for part, counts in parts.items()]
        if rows:
            st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        md = path.with_suffix(".md")
        if md.exists():
            with st.expander("Full report"):
                st.markdown(md.read_text(encoding="utf-8"))


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
st.title("Investigate, Fix or Escalate: Prototype")
tabs = st.tabs(["Live incident", "Stress test", "Triage a ticket", "All example cases", "Outbox and draft PRs",
                "Reader accuracy"])
with tabs[0]:
    live_page()
with tabs[1]:
    stress_page()
with tabs[2]:
    triage_page()
with tabs[3]:
    cases_page()
with tabs[4]:
    outbox_page()
with tabs[5]:
    accuracy_page()
