"""A free language model for the reader and the delegate: Ollama on this machine by default.

Same form, same rules and the same safeguards as the Claude reader (src/prototype/llm.py): the
answer is constrained to the form's JSON schema, the text is redacted first, and a finding whose
quote is not in the ticket or logs is discarded. Only the call to the model differs.

    winget install Ollama.Ollama
    ollama pull qwen3:4b

Settings (environment variables):
    TRIAGE_LLM_URL    default http://localhost:11434 (Ollama). Nothing leaves the machine.
    TRIAGE_LLM_MODEL  default qwen3:4b
    TRIAGE_LLM_KEY    optional. When set, the URL is treated as an OpenAI-compatible endpoint, for
                      example https://api.groq.com/openai/v1 (Groq's free tier). The text then goes
                      to that service: fictional tickets only.
"""
import json
import os

import requests

from src.prototype.delegate import SCHEMA as DELEGATE_SCHEMA, SYSTEM as DELEGATE_SYSTEM, ClaudeDelegate
from src.prototype.llm import SYSTEM as READER_SYSTEM, ClaudeReader, ReaderError

DEFAULT_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen3:4b"


def settings():
    return {"url": os.environ.get("TRIAGE_LLM_URL", DEFAULT_URL).rstrip("/"),
            "model": os.environ.get("TRIAGE_LLM_MODEL", DEFAULT_MODEL),
            "key": os.environ.get("TRIAGE_LLM_KEY") or None}


class LocalLLM:
    """One JSON-schema-constrained call. `chat(system, prompt, schema)` returns the parsed object."""

    def __init__(self, url=None, model=None, key=None, timeout=600):
        s = settings()
        self.url, self.model = (url or s["url"]).rstrip("/"), model or s["model"]
        self.key = key if key is not None else s["key"]
        self.timeout = timeout

    @property
    def label(self):
        return self.model if self.key is None else f"{self.model} (remote)"

    def chat(self, system, prompt, schema):
        messages = [{"role": "system", "content": system}, {"role": "user", "content": prompt}]
        try:
            if self.key is None:          # Ollama's own API: format takes the JSON schema itself
                r = requests.post(f"{self.url}/api/chat", timeout=self.timeout, json={
                    "model": self.model, "messages": messages, "stream": False, "format": schema,
                    "think": False, "options": {"temperature": 0, "num_ctx": 8192}})
                r.raise_for_status()
                text = r.json()["message"]["content"]
            else:                         # OpenAI-compatible (Groq and others)
                r = requests.post(f"{self.url}/chat/completions", timeout=self.timeout,
                                  headers={"Authorization": f"Bearer {self.key}"}, json={
                                      "model": self.model, "messages": messages, "temperature": 0,
                                      "response_format": {"type": "json_schema", "json_schema": {
                                          "name": "form", "schema": schema}}})
                r.raise_for_status()
                text = r.json()["choices"][0]["message"]["content"]
        except requests.ConnectionError as error:
            raise ReaderError(f"No language model at {self.url}. Start Ollama, or pick the keyword reader.") from error
        except requests.HTTPError as error:
            raise ReaderError(f"The language model refused the request: {error.response.text[:300]}") from error
        try:
            return json.loads(text)
        except json.JSONDecodeError as error:
            raise ReaderError("The language model's answer was not valid JSON.") from error


def status(llm=None):
    """(ready, message): whether the model can be called, without calling it."""
    llm = llm or LocalLLM()
    if llm.key is not None:
        return True, f"{llm.model} at {llm.url}"
    try:
        tags = requests.get(f"{llm.url}/api/tags", timeout=3).json().get("models", [])
    except (requests.RequestException, ValueError):
        return False, "Ollama is not running. Start it from the Start menu, or run `ollama serve`."
    names = {t["name"] for t in tags} | {t["name"].removesuffix(":latest") for t in tags}
    if llm.model not in names:
        return False, f"Ollama is running but {llm.model} is not downloaded: run `ollama pull {llm.model}`."
    return True, f"{llm.model}, on this machine"


EXAMPLE = """Example.
<ticket>
Since 9am staff say the fees page shows an error screen. This is the staging server.
</ticket>
<logs>
2026-11-02T09:01:00Z ERROR api    GET /api/fees/12 500 duration=0.4s
2026-11-02T09:02:00Z INFO  pool   db_pool in_use=19/20 (95%)
</logs>
Answer:
{"category": "Application and interface", "summary": "Fees page shows an error screen on staging",
 "symptoms_shown": [{"symptom": "S01 Users see a server error on a page", "quote": "the fees page shows an error screen"}],
 "context": {"X01 Affected system is production": {"value": "No", "quote": "This is the staging server."},
             "X02 Priority": {"value": "not_stated", "quote": ""}},
 "check_results": [{"check": "D03 DB connection pool usage", "result": "positive",
                    "quote": "db_pool in_use=19/20 (95%)"}]}"""


class LocalReader(ClaudeReader):
    """The Claude reader's form, but asked in a shape a small local model fills reliably: lists
    of only what the text shows, items named in full rather than by bare id, and one worked
    example. The answer is turned back into the full form, so the same quote check applies."""

    def __init__(self, model, config, llm=None):
        self.llm = llm or LocalLLM()
        super().__init__(model, config, client=object())
        self.name = f"local ({self.llm.label})"
        from src.prototype.llm import read_checks
        self.symptom_names = {f"{s['id']} {s['name']}": s["id"] for s in model["symptoms"]}
        self.check_names = {f"{c['id']} {c['name']}": c["id"] for c in read_checks(model)}
        self.context_names = {f"{a['id']} {a['name']}": a for a in model["context"]}
        quote = {"type": "string"}
        self.compact = {
            "type": "object", "required": ["category", "summary", "symptoms_shown", "context", "check_results"],
            "properties": {
                "category": self.schema["properties"]["category"],
                "summary": {"type": "string"},
                "symptoms_shown": {"type": "array", "items": {
                    "type": "object", "required": ["symptom", "quote"],
                    "properties": {"symptom": {"type": "string", "enum": list(self.symptom_names)}, "quote": quote}}},
                "context": {"type": "object", "required": list(self.context_names), "properties": {
                    name: {"type": "object", "required": ["value", "quote"], "properties": {
                        "value": {"type": "string", "enum": list(a["values"]) + ["not_stated"]}, "quote": quote}}
                    for name, a in self.context_names.items()}},
                "check_results": {"type": "array", "items": {
                    "type": "object", "required": ["check", "result", "quote"],
                    "properties": {"check": {"type": "string", "enum": list(self.check_names)},
                                   "result": {"type": "string", "enum": ["positive", "negative"]},
                                   "quote": quote}}}}}

    def _ask(self, ticket, logs):
        prompt = (f"{self.description}\n\nList only what the ticket or logs show. symptoms_shown: every symptom the "
                  "ticket or logs report. check_results: only the checks the logs or ticket answer. Each quote is "
                  "copied exactly from the text.\n\n"
                  f"{EXAMPLE}\n\nNow this incident.\n<ticket>\n{ticket}\n</ticket>\n<logs>\n{logs}\n</logs>\nAnswer:")
        answer = self.llm.chat(READER_SYSTEM, prompt, self.compact)
        form = {"category": answer.get("category", "unclear"), "summary": answer.get("summary", ""),
                "symptoms": {sid: {"state": "not_mentioned", "evidence": ""} for sid in self.symptom_names.values()},
                "context": {a["id"]: {"state": "not_stated", "evidence": ""} for a in self.context_names.values()},
                "checks": {cid: {"state": "not_shown", "evidence": ""} for cid in self.check_names.values()}}
        for item in answer.get("symptoms_shown", []):
            if item.get("symptom") in self.symptom_names:
                form["symptoms"][self.symptom_names[item["symptom"]]] = {"state": "present",
                                                                          "evidence": item.get("quote", "")}
        for name, item in (answer.get("context") or {}).items():
            if name in self.context_names:
                form["context"][self.context_names[name]["id"]] = {"state": item.get("value", "not_stated"),
                                                                   "evidence": item.get("quote", "")}
        for item in answer.get("check_results", []):
            if item.get("check") in self.check_names:
                form["checks"][self.check_names[item["check"]]] = {"state": item["result"],
                                                                   "evidence": item.get("quote", "")}
        return form


class LocalDelegate(ClaudeDelegate):
    def __init__(self, llm=None):
        self.llm = llm or LocalLLM()
        self.name = f"local ({self.llm.label})"

    def _ask(self, prompt):
        return self.llm.chat(DELEGATE_SYSTEM, prompt, DELEGATE_SCHEMA)


class HybridReader:
    """The local model reads the ticket (people's words); the configured patterns read the
    monitoring log (numbers against thresholds, which small models get wrong). Symptoms the
    log shows (5xx lines, slow requests) are added from the patterns. Only the ticket is sent to
    the model, so a reading takes well under a minute on a laptop."""

    def __init__(self, model, config, llm=None):
        from src.prototype.reading import KeywordReader
        self.local, self.keyword = LocalReader(model, config, llm=llm), KeywordReader(model, config)
        self.name = f"{self.local.name} + log patterns"

    def read(self, ticket, logs):
        from src.prototype.reading import NEGATIVE, POSITIVE, PRESENT
        words = self.local.read(ticket, "")
        patterns = self.keyword.read(ticket, logs)
        for sid, finding in patterns.symptoms.items():
            if words.symptoms[sid].value != PRESENT and finding.value == PRESENT and finding.source == "logs":
                words.symptoms[sid] = finding
        for cid, finding in patterns.checks.items():
            if finding.source == "logs" or words.checks[cid].value not in (POSITIVE, NEGATIVE):
                words.checks[cid] = finding
        words.reader = self.name
        return words
