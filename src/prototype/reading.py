"""What a ticket and its logs say, in the terms of the scenario model: which symptoms are
present, the context, and the result of each check the logs can answer.

A reader only records evidence. It never names a cause or chooses an action; the agent does
that, and the safety mechanism checks it. Every finding keeps the line it came from, so a
person can see why the reader said what it did.

KeywordReader works offline from prototype_config.json. ClaudeReader (src/prototype/llm.py)
uses a language model and returns the same Reading.
"""
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta

PRESENT, ABSENT, NOT_MENTIONED = "present", "absent", "not_mentioned"
POSITIVE, NEGATIVE, NOT_SHOWN = "positive", "negative", "not_shown"
NOT_STATED = "not_stated"

TIMESTAMP = re.compile(r"^(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2})?)")


@dataclass
class Finding:
    value: str              # symptom: present / absent / not_mentioned; check: positive / negative / not_shown;
                            # context: one of the attribute's values
    evidence: str = ""      # the ticket sentence or log line it rests on
    source: str = ""        # ticket, logs, default or operator


@dataclass
class Reading:
    reader: str
    category: str
    summary: str
    symptoms: dict          # symptom id -> Finding
    context: dict           # attribute id -> Finding
    checks: dict            # check id -> Finding
    warnings: list = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text) if s.strip()]


def log_lines(logs):
    return [line.rstrip() for line in logs.splitlines() if line.strip()]


def _first_containing(texts, keywords):
    for text in texts:
        lowered = text.lower()
        for keyword in keywords:
            if keyword in lowered:
                return text
    return None


def _timestamp(line):
    match = TIMESTAMP.match(line)
    return datetime.fromisoformat(match.group(1).replace(" ", "T")) if match else None


def read_check(spec, lines):
    """One check from the logs. Positive if a line shows it (above the threshold, if it has
    one); negative if the logs cover that source and none shows it; not shown if the logs
    say nothing about it."""
    covered = [line for line in lines if re.search(spec["covers"], line, re.I)]
    if not covered:
        return Finding(NOT_SHOWN, source="logs")
    if spec.get("within_hours") is not None:
        # The window ends at the newest line in the logs, not at the time of reading.
        stamps = [t for t in map(_timestamp, lines) if t is not None]
        if stamps:
            since = max(stamps) - timedelta(hours=spec["within_hours"])
            recent = [line for line in covered if (_timestamp(line) or since) >= since]
            if not recent:
                return Finding(NEGATIVE, covered[-1], "logs")
            covered = recent

    hits = [(line, re.search(spec["positive"], line, re.I)) for line in covered]
    hits = [(line, match) for line, match in hits if match]
    if "above" not in spec:
        return Finding(POSITIVE, hits[0][0], "logs") if hits else Finding(NEGATIVE, covered[-1], "logs")

    values = [(float(match.group("value")), line) for line, match in hits]
    if not values:
        return Finding(NEGATIVE, covered[-1], "logs")
    if spec.get("aggregate") == "median":
        ordered = sorted(values)
        value, line = ordered[len(ordered) // 2]
    else:
        value, line = max(values)
    return Finding(POSITIVE if value > spec["above"] else NEGATIVE, line, "logs")


def read_ticket_check(spec, ticket_sentences):
    for value, keywords in ((POSITIVE, spec["ticket_positive"]), (NEGATIVE, spec["ticket_negative"])):
        quote = _first_containing(ticket_sentences, keywords)
        if quote:
            return Finding(value, quote, "ticket")
    return Finding(NOT_SHOWN, source="ticket")


def apply_defaults(reading, model, config):
    """Context the ticket does not state takes the configured default; symptoms not
    mentioned count as absent, as in training, where every symptom is reported."""
    for attribute in model["context"]:
        finding = reading.context.get(attribute["id"])
        if finding is None or finding.value not in attribute["values"]:
            value = config["context_defaults"][attribute["id"]]
            reading.context[attribute["id"]] = Finding(value, config["context_defaults_reason"], "default")
    for symptom in model["symptoms"]:
        reading.symptoms.setdefault(symptom["id"], Finding(NOT_MENTIONED))
    for check in model["checks"]:
        reading.checks.setdefault(check["id"], Finding(NOT_SHOWN))
    return reading


class KeywordReader:
    """Offline reader: keyword lists for the ticket and regular expressions for the logs.
    Nothing leaves the machine."""
    name = "keyword"

    def __init__(self, model, config):
        self.model, self.config = model, config

    def read(self, ticket, logs):
        config, said, lines = self.config, sentences(ticket), log_lines(logs)

        scores = {name: sum(ticket.lower().count(k) for k in keywords)
                  for name, keywords in config["categories"].items()}
        best = max(scores, key=scores.get)
        category = best if scores[best] > 0 else "unclear"

        symptoms = {}
        for symptom in self.model["symptoms"]:
            spec = config["symptoms"][symptom["id"]]
            quote = _first_containing(said, spec["ticket"])
            if quote:
                symptoms[symptom["id"]] = Finding(PRESENT, quote, "ticket")
                continue
            line = next((l for l in lines if re.search(spec["logs"], l, re.I)), None)
            symptoms[symptom["id"]] = Finding(PRESENT, line, "logs") if line else Finding(NOT_MENTIONED)

        context = {}
        for attribute in self.model["context"]:
            for value, keywords in config["context"][attribute["id"]].items():
                quote = _first_containing(said, keywords)
                if quote:
                    context[attribute["id"]] = Finding(value, quote, "ticket")
                    break

        checks = {}
        for check in self.model["checks"]:
            if check.get("delegated"):              # answered only when the agent asks (delegate.py)
                continue
            spec = config["checks"][check["id"]]
            checks[check["id"]] = read_ticket_check(spec, said) if "ticket_positive" in spec else read_check(spec, lines)

        reading = Reading(self.name, category, said[0] if said else "", symptoms, context, checks)
        return apply_defaults(reading, self.model, config)
