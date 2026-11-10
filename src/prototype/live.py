"""Live incidents: a hidden fault, fresh evidence every time, checks answered when asked.

The example cases in prototype/examples are written by hand, so they show what was written into
them. Here an incident is drawn from the scenario model, exactly as the training environment
draws one (cause from the prior, context, symptoms, check results with p_noise reversals), and
then written out as text: a helpdesk ticket and a monitoring log with background lines and near
misses. The cause stays hidden until reveal; nobody, the presenter included, has seen it.

The agent then works on the text through the ordinary pipeline (reader -> agent -> safety
mechanism), with three differences from the example cases:
- A check the logs do not cover is answered by a probe of the hidden system when the agent asks
  for it (Probe), so each result arrives with the console output it came from.
- A fix is verified against the hidden fault (LiveVerifier): for a code fault, the patch goes
  through the staging tests against the hidden fault's reproduction tests; otherwise the
  symptoms are re-measured, and they clear only if the fix was for the hidden cause.
- "Your own ticket": a person writes the ticket; the reader's symptoms and context fix those of
  the hidden system, and the cause is drawn given them.

This is the agent's own world (the scenario model). It shows the pipeline working on incidents
nobody wrote, not that the model fits the Directorate's incidents.
"""
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

from src.prototype.reading import NEGATIVE, POSITIVE, PRESENT, Finding
from src.prototype.verify import ChainVerifier, StagingVerifier, Verification

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "prototype" / "examples"

PAGES = ["student portal", "results page", "fees page", "course registration page", "transcripts page",
         "timetable page", "library account page", "hostel booking page"]
PATHS = ["/api/students/{n}", "/api/results/{n}", "/api/fees/{n}", "/api/courses/{n}", "/api/transcripts/{n}",
         "/api/timetable/{n}", "/api/library/{n}", "/api/hostels/{n}"]
REPORTERS = ["the helpdesk", "the Registrar's office", "the Bursar's office", "a lecturer", "the faculty administrator",
             "the student guild", "the Dean of Students' office"]
# Not portal/cache.py or portal/db.py: the keyword reader would count those lines as cache or db lines.
CODE_FILES = ["portal/auth.py", "portal/results.py", "portal/payments.py", "portal/http.py"]
FUNCS = {"portal/auth.py": "sign_in", "portal/results.py": "class_results", "portal/payments.py": "charge",
         "portal/cache.py": "get_or_compute", "portal/http.py": "handle", "portal/db.py": "execute"}


# ----- The hidden incident -----------------------------------------------------------------
@dataclass
class Incident:
    seed: int
    origin: str                  # "random", "chosen" or "your ticket"
    cause: str                   # hidden until reveal
    context: dict                # attribute id -> value
    symptoms: dict               # symptom id -> present?
    true_results: dict           # check id -> what the system really shows
    results: dict                # check id -> what a check reports (true result, maybe reversed)
    in_logs: list                # checks the monitoring log covers from the start
    in_ticket: list              # checks the ticket answers (D10)
    ticket: str
    logs: str
    started: str
    probes: dict = field(default_factory=dict)    # check id -> console output, filled when asked

    @property
    def reversed(self):
        return [k for k in self.results if self.results[k] != self.true_results[k]]

    def to_dict(self):
        return asdict(self)


def _rng(seed):
    return np.random.default_rng(seed)


def _pick(rng, items):
    return items[int(rng.integers(len(items)))]


def draw(model, scenario, seed, cause=None, symptoms=None, context=None, ticket=None, known=None, monitored=0.55):
    """An incident as the training environment draws one. `cause` (an id) is the fault someone
    chose; `symptoms` and `context` (from a reading of someone's own ticket) fix those, and the
    cause is then drawn given them. `monitored` is the chance that the monitoring log covers a
    check from the start; the rest are answered by probes."""
    rng = _rng(seed)
    cause_ids = [c["id"] for c in model["causes"]]
    attrs = model["context"]
    if context is None:
        context = {a["id"]: a["values"][int(rng.choice(len(p), p=p))]
                   for a, p in zip(attrs, scenario.context_probs)}
    origin = "your ticket" if ticket is not None else ("chosen" if cause else "random")

    if symptoms is not None:
        present = np.array([symptoms[s["id"]] for s in model["symptoms"]], dtype=bool)
        weight = scenario.prior * np.prod(np.where(present[:, None], scenario.symptom_theta,
                                                   1 - scenario.symptom_theta), axis=0)
        reported_theta = scenario.theta * (1 - scenario.p_noise) + (1 - scenario.theta) * scenario.p_noise
        for i, c in enumerate(model["checks"]):
            if c["id"] in (known or {}):
                weight = weight * (reported_theta[i] if known[c["id"]] else 1 - reported_theta[i])
        j = int(rng.choice(len(weight), p=weight / weight.sum())) if cause is None else cause_ids.index(cause)
    else:
        j = int(rng.choice(scenario.n_causes, p=scenario.prior)) if cause is None else cause_ids.index(cause)
        # A ticket reports at least one symptom, so redraw an incident with none.
        for _ in range(50):
            present = rng.random(scenario.n_symptoms) < scenario.symptom_theta[:, j]
            if present.any():
                break
        else:
            present[int(np.argmax(scenario.symptom_theta[:, j]))] = True

    true = rng.random(scenario.n_checks) < scenario.theta[:, j]
    reported = true ^ (rng.random(scenario.n_checks) < scenario.p_noise)
    checks = model["checks"]
    true_results = {c["id"]: bool(t) for c, t in zip(checks, true)}
    results = {c["id"]: bool(r) for c, r in zip(checks, reported)}
    for cid, value in (known or {}).items():    # what someone's own ticket says stands
        results[cid] = true_results[cid] = bool(value)
    symptoms = {s["id"]: bool(p) for s, p in zip(model["symptoms"], present)}

    in_logs, in_ticket = [], []
    for c in checks:
        if c.get("delegated"):
            in_logs.append(c["id"])            # stack traces are always in the log
        elif c["id"] == "D10":
            if ticket is None and rng.random() < 0.6:
                in_ticket.append("D10")
        elif ticket is None and rng.random() < monitored:
            in_logs.append(c["id"])
    if "D05" in in_logs and "D02" not in in_logs:
        in_logs.append("D02")                  # D05's line is a db line, which D02 reads too

    start = datetime.now().replace(second=0, microsecond=0) - timedelta(minutes=int(rng.integers(8, 40)))
    incident = Incident(int(seed), origin, cause_ids[j], context, symptoms, true_results, results,
                        sorted(in_logs), in_ticket, "", "", start.isoformat())
    incident.ticket = ticket if ticket is not None else write_ticket(incident, rng)
    incident.logs = write_logs(incident, rng, only_traces=ticket is not None)
    return incident


# ----- Writing the evidence --------------------------------------------------------------------
SYMPTOM_LINES = {
    "S01": ["Users get an error page when they open the {page}.",
            "The {page} shows an error screen that says something went wrong.",
            "People see a server error on the {page}.",
            "Opening the {page} shows an error instead of the page."],
    "S02": ["The {page} is very slow and sometimes times out.",
            "The {page} takes forever to load.",
            "The {page} hangs and is often not loading at all."],
    "S03": ["Several people cannot log in at all.",
            "Users are logged out again a few seconds after signing in.",
            "Students say the login fails with a message."],
    "S04": ["When staff press save, it spins for about a minute and then fails.",
            "Approvals spin for ages and then fail after a long wait.",
            "Saving a record spins and then errors."],
}
X01_LINES = {"Yes": ["This is the production system.", "It is on the live site.", "This is prod."],
             "No": ["We saw it on the staging server.", "This is the test environment, not production.",
                    "It is happening on the UAT server."]}
X02_LINES = {"High": ["Priority: high.", "It is urgent.", "This is critical for us today."],
             "Medium": ["Priority: medium."],
             "Low": ["Priority: low.", "It is minor, look at it when you get a chance."]}
D10_LINES = {True: ["Only some records seem affected; others are fine.", "It happens only for certain students.",
                    "A few students have it, others can carry on."],
             False: ["It happens for all users we have asked.", "Nobody can get through.",
                     "It is the same for every user."]}
SUBJECTS = {"S01": "Error on the {page}", "S02": "{Page} very slow", "S03": "Login problems",
            "S04": "Saves failing on the {page}"}


def write_ticket(incident, rng):
    page = _pick(rng, PAGES)
    present = [s for s, p in incident.symptoms.items() if p]
    order = list(rng.permutation(present))
    body = [_pick(rng, SYMPTOM_LINES[s]).format(page=page) for s in order]
    started = datetime.fromisoformat(incident.started)
    body.insert(0, f"Since about {started:%H:%M} today, reported by {_pick(rng, REPORTERS)}.")
    if "D10" in incident.in_ticket:
        body.append(_pick(rng, D10_LINES[incident.results["D10"]]))
    x01, x02 = incident.context["X01"], incident.context["X02"]
    if x01 == "No" or rng.random() < 0.8:           # left out only when it is the default
        body.append(_pick(rng, X01_LINES[x01]))
    if x02 != "High" or rng.random() < 0.8:
        body.append(_pick(rng, X02_LINES[x02]))
    subject = SUBJECTS[order[0]].format(page=page, Page=page.capitalize())
    number = int(rng.integers(40000, 49999))
    return f"Subject: {subject} (ticket #{number})\n\n" + " ".join(body)


def _ts(t):
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def _line(t, level, source, message):
    return f"{_ts(t)} {level:<5} {source:<6} {message}"


def _evidence_lines(cid, positive, t, rng, symptoms):
    """Monitoring lines for one check, in the log format the keyword reader is set up for.
    Negative results are often near misses: below the threshold, or outside the window."""
    u = lambda a, b: float(rng.uniform(a, b))                                  # noqa: E731
    slow = symptoms["S02"]
    if cid == "D01":
        d = (u(14, 45) if slow else u(11, 19.5)) if positive else u(0.2, 9.5)
        return [_line(t, "INFO", "span", f"outbound POST gateway/{_pick(rng, ['charge', 'verify', 'sms'])} "
                                         f"duration={d:.1f}s")]
    if cid == "D02":
        if positive:
            return [_line(t, "WARN", "db", _pick(rng, ['could not obtain lock on row in relation "results"',
                                                       "deadlock detected while updating users.last_token",
                                                       "lock wait timeout exceeded on table approvals"]))]
        return [_line(t, "INFO", "db", f"replication lag {u(0.1, 0.9):.1f}s")]
    if cid == "D03":
        pct = int(u(82, 100)) if positive else int(u(25, 78))
        n = round(pct / 5)
        return [_line(t, "INFO", "pool", f"db_pool in_use={n}/20 ({pct}%)")]
    if cid == "D04":
        lo, hi = (84, 98) if positive else (20, 76)
        return [_line(t, "INFO", "node", f"api-{k} cpu={int(u(lo, hi))}%") for k in (1, 2, 3)]
    if cid == "D05":
        age = int(u(90, 900)) if positive else int(u(1, 45))
        return [_line(t, "INFO", "db", f"active_transactions={int(u(4, 14))} oldest_tx_age={age}s")]
    if cid == "D06":
        plan = "Seq Scan on enrolments (rows=2.1M)" if positive else "Index Scan using enrolments_student_idx"
        return [_line(t, "INFO", "sql", f"plan of slowest query: {plan}")]
    if cid == "D07":
        q = int(u(180, 600)) if positive else int(u(6, 60))
        d = u(20, 29) if slow else u(0.4, 1.8)
        return [_line(t, "INFO", "span", f"trace GET /api/classes/{int(u(2, 40))}/summary duration={d:.1f}s queries={q}")]
    if cid == "D08":
        if positive:
            return [_line(t, "WARN", "cache", f"set failed for key profile:{int(u(100, 999))}: "
                                              "TypeError: Object of type date is not JSON serializable")]
        return [_line(t, "INFO", "cache", f"hit_rate={u(0.88, 0.99):.2f}")]
    if cid == "D09":
        hours = u(1, 6) if positive else u(30, 240)
        when = t - timedelta(hours=hours)
        what = _pick(rng, ["release v3.9.1 deployed", "migration 0142_add_hold_flags applied"])
        return [(when, _line(when, "INFO", "deploy", what))]
    raise KeyError(cid)


def _traceback(positive, t, rng):
    if positive:
        path = _pick(rng, CODE_FILES)
        frame = f'  File "{path}", line {int(rng.integers(12, 140))}, in {FUNCS[path]}'
    else:
        frame = (f'  File "/usr/lib/python3.11/site-packages/'
                 f'{_pick(rng, ["psycopg/cursor.py", "redis/connection.py", "httpx/_client.py"])}", '
                 f'line {int(rng.integers(200, 900))}, in {_pick(rng, ["execute", "send", "read_response"])}')
    return [_line(t, "ERROR", "api", "Traceback (most recent call last):"), _line(t, "ERROR", "api", frame)]


def _request_lines(t, rng, symptoms):
    """What users hit, consistent with the symptoms (the keyword reader reads these too)."""
    s01, s02, s03, s04 = (symptoms[k] for k in ("S01", "S02", "S03", "S04"))
    out = []
    for _ in range(int(rng.integers(2, 5))):
        path = _pick(rng, PATHS).format(n=int(rng.integers(100, 9999)))
        if s01:
            d = rng.uniform(20, 29) if s02 else rng.uniform(0.3, 1.9)
            out.append(_line(t, "ERROR", "api", f"GET {path} 500 duration={d:.1f}s"))
        elif s02:
            out.append(_line(t, "WARN", "api", f"GET {path} 200 duration={rng.uniform(20, 38):.1f}s"))
        t += timedelta(seconds=int(rng.integers(3, 40)))
    if s03:
        code = 500 if s01 else 401
        for _ in range(int(rng.integers(1, 4))):
            out.append(_line(t, "WARN" if code == 401 else "ERROR", "api",
                             f"POST /auth/login {code} duration={rng.uniform(0.2, 1.5):.1f}s"))
            t += timedelta(seconds=int(rng.integers(2, 20)))
    if s04 and s01 and s02:
        out.append(_line(t, "ERROR", "api", f"POST /api/approvals 500 duration={rng.uniform(40, 62):.1f}s"))
    return out


def _background(t, rng):
    path = _pick(rng, PATHS).format(n=int(rng.integers(100, 9999)))
    return _pick(rng, [
        _line(t, "INFO", "api", f"GET {path} 200 duration={rng.uniform(0.05, 1.6):.2f}s"),
        _line(t, "INFO", "api", f"GET /static/app.{int(rng.integers(1000, 9999))}.js 200 duration=0.01s"),
        _line(t, "INFO", "health", "liveness ok"),
        _line(t, "INFO", "cron", f"job {_pick(rng, ['send_reminders', 'sync_registry', 'nightly_report'])} finished"),
        _line(t, "INFO", "mail", f"queued {int(rng.integers(1, 40))} notification e-mails"),
    ])


def write_logs(incident, rng, only_traces=False):
    """The monitoring log: background traffic, the users' failing requests, the lines for the
    checks the log covers, and the stack traces the delegated analysis reads."""
    start = datetime.fromisoformat(incident.started)
    lines = []                                   # (time, text)
    t = start
    if not only_traces:
        for _ in range(int(rng.integers(14, 24))):
            lines.append((t, _background(t, rng)))
            t += timedelta(seconds=int(rng.integers(5, 70)))
        for text in _request_lines(start + timedelta(minutes=1), rng, incident.symptoms):
            lines.append((datetime.fromisoformat(text[:19]), text))
        for cid in incident.in_logs:
            if cid == "D11":
                continue
            when = start + timedelta(seconds=int(rng.integers(30, 900)))
            for item in _evidence_lines(cid, incident.results[cid], when, rng, incident.symptoms):
                lines.append(item if isinstance(item, tuple) else (when, item))
    when = start + timedelta(seconds=int(rng.integers(60, 600)))
    for text in _traceback(incident.results["D11"], when, rng):
        lines.append((when, text))
    lines.sort(key=lambda x: x[0])
    return "\n".join(text for _, text in lines)


# ----- Answering checks and verifying fixes ------------------------------------------------------
PROBES = {
    "D01": "trace-query --slowest --outbound",
    "D02": "grep -c 'lock' /var/log/postgresql/postgresql.log",
    "D03": "pool-stats db_pool",
    "D04": "top -b -n1 | head (api nodes)",
    "D05": "psql -c \"SELECT max(now() - xact_start) FROM pg_stat_activity\"",
    "D06": "psql -c \"EXPLAIN <slowest query>\"",
    "D07": "trace-query --slowest --count-queries",
    "D08": "redis-cli info stats; grep cache /var/log/portal/app.log",
    "D09": "git log --since=24.hours --oneline deploy/production",
    "D10": "error-scope --last 30m",
}


class Probe:
    """`ask` for triage(): answers a check the reader did not find, from the hidden system, with
    the console output the answer came from. Every call is recorded in incident.probes."""

    def __init__(self, incident, seed_offset=7):
        self.incident = incident
        self.rng = _rng(incident.seed + seed_offset)

    def __call__(self, check):
        cid = check["id"]
        positive = self.incident.results[cid]
        if cid == "D10":
            out = ("errors for 37 of 2,140 active users (1.7%), all on the same records" if positive
                   else "errors for 1,912 of 2,140 active users (89%)")
        else:
            t = datetime.fromisoformat(self.incident.started) + timedelta(minutes=20)
            lines = _evidence_lines(cid, positive, t, self.rng, self.incident.symptoms)
            out = "\n".join(x[1] if isinstance(x, tuple) else x for x in lines)
        text = f"$ {PROBES[cid]}\n{out}"
        self.incident.probes[cid] = text
        return Finding(POSITIVE if positive else NEGATIVE, text, "probe")


SYMPTOM_MEASURES = {"S01": ("5xx rate", "{:.1f}%"), "S02": ("p95 response time", "{:.1f} s"),
                    "S03": ("failed sign-ins", "{:.0f}/min"), "S04": ("failed saves", "{:.0f}/min")}


class Remeasure:
    """After a fix, the symptoms are measured again on the hidden system. They clear exactly when
    the fix was for the hidden cause, as in training."""

    def __init__(self, incident):
        self.incident = incident
        self.rng = _rng(incident.seed + 11)

    def __call__(self, cause, report):
        cleared = cause["id"] == self.incident.cause
        parts = []
        for sid, present in self.incident.symptoms.items():
            if not present:
                continue
            name, fmt = SYMPTOM_MEASURES[sid]
            bad = {"S01": self.rng.uniform(8, 40), "S02": self.rng.uniform(18, 45),
                   "S03": self.rng.uniform(20, 90), "S04": self.rng.uniform(5, 30)}[sid]
            good = {"S01": self.rng.uniform(0, 0.3), "S02": self.rng.uniform(0.3, 1.2),
                    "S03": 0, "S04": 0}[sid]
            parts.append(f"{name} {fmt.format(good if cleared else bad)}")
        detail = ("re-measured for 10 minutes after the remedy: " + ", ".join(parts)
                  + (" (back to normal)" if cleared else " (unchanged)"))
        return Verification(cleared, "re-measured", detail)


def reproduction_tests():
    """Cause id -> the toy repository's reproduction tests for it, from the example cases."""
    cases = json.loads((EXAMPLES / "cases.json").read_text(encoding="utf-8"))["cases"]
    out = {}
    for name, case in cases.items():
        path = EXAMPLES / name / "verification.json"
        if case.get("intended_cause") and path.exists():
            out[case["intended_cause"]] = json.loads(path.read_text(encoding="utf-8"))["reproduce"]
    return out


def live_verifier(incident, actions_settings, staging=True, patcher="pre-written"):
    """Staging tests when the hidden fault is a code fault with reproduction tests (any code
    patch, right or wrong, is applied and judged by them); otherwise re-measuring."""
    chain = []
    if staging:
        from src.prototype.actions import ClaudePatcher, PrewrittenPatcher
        repro = reproduction_tests().get(incident.cause, [])
        if repro:
            maker = ClaudePatcher() if patcher == "claude" else PrewrittenPatcher(ROOT / actions_settings["fixes"])
            chain.append(StagingVerifier(ROOT / actions_settings["toy_repo"], maker, repro))
    chain.append(Remeasure(incident))
    return ChainVerifier(*chain)


# ----- Running and scoring ------------------------------------------------------------------------
def reading_errors(reading, incident, model):
    """Where the reader's form differs from the hidden system (for the reveal)."""
    errors = []
    for s in model["symptoms"]:
        said = reading.symptoms[s["id"]].value == PRESENT
        if said != incident.symptoms[s["id"]]:
            errors.append(f"{s['id']} {s['name']}: read as {'present' if said else 'absent'}")
    for a in model["context"]:
        f = reading.context[a["id"]]
        if f.value != incident.context[a["id"]]:
            errors.append(f"{a['id']} {a['name']}: read as {f.value}" + (" (default)" if f.source == "default" else ""))
    for c in model["checks"]:
        f = reading.checks[c["id"]]
        if f.value in (POSITIVE, NEGATIVE) and (f.value == POSITIVE) != incident.results[c["id"]]:
            errors.append(f"{c['id']} {c['name']}: read as {f.value}")
    return errors


def hindsight(incident, model, scenario):
    """The most probable cause given every check result: where perfect investigation would point.
    When it is not the hidden cause, the evidence itself misleads, and escalating is sound."""
    from src.agents.belief import posterior
    from src.sim.triage_env import TriageEnv
    status = np.array([TriageEnv.POSITIVE if incident.results[c["id"]] else TriageEnv.NEGATIVE
                       for c in model["checks"]])
    symptoms = np.array([incident.symptoms[s["id"]] for s in model["symptoms"]])
    reported_theta = scenario.theta * (1 - scenario.p_noise) + (1 - scenario.theta) * scenario.p_noise
    belief = posterior(scenario, reported_theta, status, symptoms)
    j = int(np.argmax(belief))
    return model["causes"][j]["id"], float(belief[j])


def outcome(report, incident):
    """One word for the scoreboard."""
    d = report["decision"]
    if d["outcome"] == "fix":
        failed = sum(a["cleared"] is False for a in d.get("attempts", []))
        if d["cause"] == incident.cause:
            return "resolved" if not failed else "resolved after a failed fix"
        return "wrong fix"                       # cannot happen with verification
    if d["outcome"] == "awaiting_verification":
        return "awaiting verification"
    return "escalated after failed fixes" if d["outcome"] == "fix_limit" else "escalated"


def from_ticket(reading, ticket, model, scenario, seed):
    """Someone's own ticket: the hidden system takes the symptoms, context and check results the
    reader found in it, and the cause is drawn given them."""
    symptoms = {k: f.value == PRESENT for k, f in reading.symptoms.items()}
    if not any(symptoms.values()):
        raise ValueError("The reader found no symptom in this ticket, so there is nothing to investigate.")
    context = {k: f.value for k, f in reading.context.items()}
    known = {k: f.value == POSITIVE for k, f in reading.checks.items() if f.value in (POSITIVE, NEGATIVE)}
    return draw(model, scenario, seed, symptoms=symptoms, context=context, ticket=ticket, known=known)


def run(incident, reader, scenario, model, agent, config, delegate=None, staging=True, patcher="pre-written",
        reading=None, read_seconds=0.0):
    """The ordinary pipeline on a live incident. Returns (reading, report). `reading` is given
    when the ticket was read already (someone's own ticket)."""
    import time

    from src.prototype.triage import triage
    if reading is None:
        t0 = time.perf_counter()
        reading = reader.read(incident.ticket, incident.logs)
        read_seconds = time.perf_counter() - t0
    verify = live_verifier(incident, config["actions"], staging, patcher) if scenario.verify else None
    t1 = time.perf_counter()
    report = triage(reading, scenario, model, agent, ask=Probe(incident), delegate=delegate,
                    ticket=incident.ticket, logs=incident.logs, verify=verify)
    report["timing"] = {"read_seconds": round(read_seconds, 1),
                        "decide_seconds": round(time.perf_counter() - t1, 1)}
    return reading, report
