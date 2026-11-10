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
import subprocess
import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.agents.dqn import MaskedDQN                                      # noqa: E402
from src.prototype.cli import load_inputs, make_reader                    # noqa: E402
from src.prototype.delegate import make_delegate                          # noqa: E402
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
    reader_name = st.radio("Reader", ["keyword", "claude"], horizontal=True, disabled=not key,
                           help="keyword runs offline. claude sends the redacted text to the Claude API.")
    delegate_name = st.radio("Delegate (D11)", ["pattern", "claude", "off"], horizontal=True,
                             help="Who answers a delegated full log analysis.")
    if not key:
        st.caption("No ANTHROPIC_API_KEY set, so the Claude reader, delegate and patcher are off.")
        reader_name = "keyword"
        delegate_name = "pattern" if delegate_name == "claude" else delegate_name
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


# ----- Layout ----------------------------------------------------------------
st.title("Investigate, Fix or Escalate: Prototype")
tabs = st.tabs(["Triage a ticket", "All example cases", "Outbox and draft PRs", "Reader accuracy"])
with tabs[0]:
    triage_page()
with tabs[1]:
    cases_page()
with tabs[2]:
    outbox_page()
with tabs[3]:
    accuracy_page()
