"""Training dashboard for the pilot.

    streamlit run dashboard/app.py

Training: live charts of a run, read from results/pilot/runs/<run>/metrics.jsonl.
Thinking: step through one incident with any saved checkpoint and see the agent's value for
every action beside the exact optimal values and what the evidence says about the cause.
"""
import json
import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.agents.dqn import MaskedDQN                           # noqa: E402
from src.agents.monitoring import MONITOR_SEED                 # noqa: E402
from dashboard.thinking import exact_for, load_run_scenario, trace  # noqa: E402

RUNS = ROOT / "results" / "pilot" / "runs"
COLOURS = {"correct": "#2e7d32", "wrong": "#c62828", "escalated": "#9e9e9e"}

st.set_page_config(page_title="Triage Agent Training", layout="wide")


# ----- Data ------------------------------------------------------------------
def list_runs():
    if not RUNS.exists():
        return []
    return sorted((p for p in RUNS.iterdir() if (p / "config.json").exists()),
                  key=lambda p: p.stat().st_mtime, reverse=True)


def read_config(run):
    return json.loads((run / "config.json").read_text(encoding="utf-8"))


def read_metrics(run):
    path = run / "metrics.jsonl"
    if not path.exists():
        return pd.DataFrame()
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return pd.DataFrame(rows)


def warnings_for(df, config):
    """The warning signs agreed in the pilot plan (Phase 4)."""
    if df.empty:
        return []
    last, found = df.iloc[-1], []
    if last["step"] >= 100_000 and last["escalation_rate"] > 0.8:
        found.append("Over 80% escalated after 100,000 steps: likely stuck on always escalating.")
    if last["step"] >= 100_000 and last["mean_checks"] < 1:
        found.append("Under 1 check per incident after 100,000 steps: it is not investigating.")
    exact = config.get("exact_value")
    if exact is not None and last["wrong_rate"] > 0.25 and last["learned_start_value"] > exact + 0.3:
        found.append("Many wrong fixes and a learned value above the exact value: likely overestimation "
                     "(try Double DQN).")
    if config["agent"] == "shielded" and last.get("executed_violation_rate", 0) > 0:
        found.append("A prohibited action executed under the safety mechanism. This is a bug.")
    return found


# ----- Charts ----------------------------------------------------------------
def panel(container, title, note, chart):
    """A fixed heading above the chart, outside the plot, so it is never cut off and does not
    move when the chart redraws."""
    container.markdown(f"##### {title}")
    container.caption(note)
    container.altair_chart(chart, width="stretch")


def line_chart(df, columns, y_title, references=None, percent=False):
    long = df.melt("step", value_vars=columns, var_name="series", value_name="value").dropna()
    axis = alt.Axis(format="%") if percent else alt.Axis()
    chart = alt.Chart(long).mark_line(point=True).encode(
        x=alt.X("step:Q", title="Training step"),
        y=alt.Y("value:Q", title=y_title, axis=axis),
        color=alt.Color("series:N", title=None, legend=alt.Legend(orient="bottom")),
        tooltip=["step", "series", alt.Tooltip("value:Q", format=".3f")])
    layers = [chart]
    if references:
        ref = pd.DataFrame([{"label": k, "value": v} for k, v in references.items() if v is not None])
        if not ref.empty:
            layers.append(alt.Chart(ref).mark_rule(strokeDash=[4, 4]).encode(
                y="value:Q", color=alt.value("#555"), tooltip=["label", alt.Tooltip("value:Q", format=".3f")]))
            layers.append(alt.Chart(ref).mark_text(align="left", dx=4, dy=-6, fontSize=11, color="#555").encode(
                y="value:Q", x=alt.value(0), text="label"))
    return alt.layer(*layers).properties(height=260)


def outcome_chart(df):
    mix = pd.DataFrame({"step": df["step"], "correct": df["resolution_accuracy"],
                        "wrong": df["wrong_rate"], "escalated": df["escalation_rate"]})
    long = mix.melt("step", var_name="outcome", value_name="share")
    return alt.Chart(long).mark_area().encode(
        x=alt.X("step:Q", title="Training step"),
        y=alt.Y("share:Q", stack="normalize", title="Share of incidents", axis=alt.Axis(format="%")),
        color=alt.Color("outcome:N", scale=alt.Scale(domain=list(COLOURS), range=list(COLOURS.values())),
                        legend=alt.Legend(orient="bottom"), title=None),
        order=alt.Order("outcome:N", sort="ascending"),
        tooltip=["step", "outcome", alt.Tooltip("share:Q", format=".1%")]
    ).properties(height=260)


# ----- Training page ---------------------------------------------------------
def training_page(run):
    config = read_config(run)
    refs = config.get("references", {})
    ref_value = lambda key: {k: v[key] for k, v in refs.items()}

    @st.fragment(run_every="5s")
    def live():
        df = read_metrics(run)
        finished = (run / "finished.json").exists()
        if df.empty:
            st.info("Waiting for the first evaluation...")
            return
        last = df.iloc[-1]
        cols = st.columns(6)
        cols[0].metric("Status", "Finished" if finished else "Training")
        cols[1].metric("Step", f"{int(last['step']):,} / {config['steps']:,}")
        cols[2].metric("Return (monitor incidents)", f"{last['mean_return']:.2f}",
                       delta=f"{last['mean_return'] - df.iloc[-2]['mean_return']:+.2f}" if len(df) > 1 else None)
        cols[3].metric("Agrees with exact", "n/a" if pd.isna(last.get("agreement_with_exact"))
                       else f"{last['agreement_with_exact']:.0%}")
        speed = last.get("steps_per_second") or 0
        remaining = (config["steps"] - last["step"]) / speed / 60 if speed and not finished else 0
        cols[4].metric("Speed", f"{speed:,.0f} steps/s")
        cols[5].metric("Time left", "-" if finished else f"about {remaining:.0f} min")

        for w in warnings_for(df, config):
            st.warning(w)

        exact_checks = refs.get("Exact optimal", {}).get("mean_checks")
        left, right = st.columns(2)
        panel(left, "Return", "Mean return on the monitoring incidents; dashed lines are the references.",
              line_chart(df, ["mean_return"], "Mean return", ref_value("mean_return")))
        panel(right, "Outcome mix", "Exact optimal: about 61% correct, 17% wrong, 22% escalated.",
              outcome_chart(df))

        left, right = st.columns(2)
        panel(left, "Checks per incident", "Dashed line: the exact optimal policy.",
              line_chart(df, ["mean_checks"], "Checks", {"Exact optimal": exact_checks}))
        panel(right, "Rules", "Blocked proposals, forced escalations and executed violations.",
              line_chart(df, ["proposed_violation_rate", "forced_escalation_rate", "executed_violation_rate"],
                         "Rate", percent=True))

        left, right = st.columns(2)
        panel(left, "Value at the start of an incident", "The agent's own estimate against the exact value.",
              line_chart(df, ["learned_start_value", "exact_start_value"], "Expected return"))
        panel(right, "Agreement with the exact policy", "Share of steps where it picks the same action.",
              line_chart(df, ["agreement_with_exact"], "Share of steps", percent=True))

        left, right = st.columns(2)
        panel(left, "Exploration rate", "Share of actions taken at random during training.",
              line_chart(df, ["exploration_rate"], "Epsilon", percent=True))
        panel(right, "Training loss", "On the scaled rewards used for training.",
              line_chart(df, ["loss"], "Loss"))

    live()


# ----- Thinking page ---------------------------------------------------------
@st.cache_resource(show_spinner="Loading checkpoint...")
def load_model(path):
    return MaskedDQN.load(path, device="cpu")


@st.cache_resource(show_spinner="Solving the exact policy for reference (about 40 seconds, once)...")
def cached_exact(model_path, settings_path, agent, p_noise, p_miss):
    return exact_for(ROOT / model_path, ROOT / settings_path, agent, p_noise, p_miss)


def thinking_page(run):
    config = read_config(run)
    checkpoints = sorted((run / "checkpoints").glob("step_*.zip"))
    if not checkpoints:
        st.info("No checkpoints yet.")
        return
    steps = [int(p.stem.split("_")[1]) for p in checkpoints]

    c1, c2, c3 = st.columns([3, 1, 2])
    chosen = c1.select_slider("Checkpoint (training step)", options=steps, value=steps[-1],
                              format_func=lambda s: f"{s:,}")
    incident = c2.number_input("Incident", min_value=0, max_value=999_999, value=0, step=1)
    scenario = load_run_scenario(ROOT, config)
    check_names = [f"D{i + 1:02d}" for i in range(scenario.n_checks)]
    flips = c3.multiselect("What if this check's result were reversed?", check_names)

    model = load_model(str(run / "checkpoints" / f"step_{chosen:07d}.zip"))
    exact = cached_exact(config["model"], config["settings"], config["agent"], config["p_noise"], config["p_miss"])
    names = json.loads((ROOT / config["model"]).read_text(encoding="utf-8"))
    steps_taken = trace(model, scenario, config["agent"], MONITOR_SEED + int(incident),
                        [check_names.index(f) for f in flips], exact)

    st.caption("The agent's values are its own estimates of the return to come. The cause probabilities and "
               "the exact values are references calculated from the ratings: the agent never sees them.")
    k = st.slider("Step", 1, len(steps_taken), 1) - 1 if len(steps_taken) > 1 else 0
    s = steps_taken[k]

    context = ", ".join(f"{a['name']}: {s['context'][i]}" for i, a in enumerate(names["context"]))
    st.markdown(f"**Incident {incident}** · {context} · step {k + 1} of {len(steps_taken)}")

    left, right = st.columns([1, 1])
    with left:
        st.markdown("**Evidence so far**")
        symptoms = pd.DataFrame({"Symptom": [x["name"] for x in names["symptoms"]],
                                 "Reported": ["present" if v else "absent" for v in s["symptoms"]]})
        st.dataframe(symptoms, hide_index=True, width="stretch")
        checks = pd.DataFrame({"Check": [f"{c['id']} {c['name']}" for c in names["checks"]],
                               "Result": s["check_status"]})
        st.dataframe(checks[checks["Result"] != "not run"], hide_index=True, width="stretch")
    with right:
        st.markdown("**What the evidence says (reference)**")
        causes = pd.DataFrame({"Cause": [f"{c['id']} {c['name']}" for c in names["causes"]],
                               "Probability": s["posterior"]})
        st.altair_chart(alt.Chart(causes).mark_bar().encode(
            x=alt.X("Probability:Q", axis=alt.Axis(format="%"), scale=alt.Scale(domain=[0, 1])),
            y=alt.Y("Cause:N", sort="-x", title=None),
            tooltip=["Cause", alt.Tooltip("Probability:Q", format=".1%")]).properties(height=230),
            width="stretch")
        if s["blocked_rules"]:
            st.markdown("**Fixes prohibited right now:** " + "; ".join(s["blocked_rules"]))

    st.markdown("**Values of each action**")
    actions = pd.DataFrame(s["actions"])
    st.dataframe(actions, hide_index=True, width="stretch",
                 column_config={"Agent value": st.column_config.NumberColumn(format="%.2f"),
                                "Exact value": st.column_config.NumberColumn(format="%.2f")})
    verdict = f"**Agent chooses:** {s['chosen']}"
    if s["margin"] is not None:
        verdict += f" · ahead of its next choice by {s['margin']:.2f}"
    if s["exact_choice"]:
        verdict += f" · exact optimal would choose: {s['exact_choice']}"
    st.markdown(verdict)
    if s.get("result"):
        st.info(s["result"])
    last = steps_taken[-1]
    st.markdown(f"**Outcome:** {last['outcome']} · return {last['total_return']:.2f} · true cause: "
                f"{names['causes'][last['cause']]['id']} {names['causes'][last['cause']]['name']} "
                f"(hidden from the agent)")


# ----- Layout ----------------------------------------------------------------
st.title("Investigate, Recommend or Escalate: Training Dashboard")
runs = list_runs()
if not runs:
    st.info("No runs yet. Start one with: python -m experiments.pilot.train_dqn")
    st.stop()
with st.sidebar:
    page = st.radio("View", ["Training", "Thinking"])
    run = st.selectbox("Run", runs, format_func=lambda p: p.name)
    st.caption("Monitoring uses its own incidents, never the evaluation incidents.")
if page == "Training":
    training_page(run)
else:
    thinking_page(run)
