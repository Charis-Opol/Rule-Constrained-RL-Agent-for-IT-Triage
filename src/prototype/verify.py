"""Fix, then verify, in the prototype (the training environment's fix_with_verification).

In training, a fix clears the symptoms exactly when it is the fix for the hidden cause. Here
the cause is unknown, so whether a fix cleared the symptoms has to come from outside. A
verifier answers that for one fix at a time, and the agent then sees what it saw in training:
the incident is resolved, or that fix is flagged as failed and the agent goes on.

Sources, tried in order by a ChainVerifier:
- StagingVerifier (code faults): the patch is applied to a throwaway copy of the toy repository,
  standing in for a staging environment, and the repository's tests are run. The patch must
  break no test, and the incident's own reproduction tests (named in the case's
  verification.json) decide whether the symptom cleared. "The patch passes its own test" is not
  enough: every planted bug is in the repository at once, so any patch fixes some test.
- AnswerVerifier: the operator says whether the symptoms cleared (standing in for the owner who
  applied the remedy and checked).
- CaseVerifier (demo only): the answer the case was written to have, from cases.json.

A verifier never acts on anything real: no pull request is opened and no message is sent here.
That happens after the final decision, in actions.py, so a fix can be verified, and the
incident replayed, without side effects.
"""
import shutil
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path

from src.prototype.actions import ActionRefused, Patch, PrewrittenPatcher, check_patch, test_outcomes


@dataclass
class Verification:
    cleared: object             # True, False, or None (nobody has said yet)
    how: str                    # "staging tests", "operator", "case (demo only)" or "none"
    detail: str
    patch: dict = field(default=None)   # code faults: the patch that was verified (path, content, ...)

    def to_dict(self):
        return asdict(self)


def _passed(outcomes, test):
    """Outcome of a test given by its full id or by its function name."""
    for name, ok in outcomes.items():
        if name == test or name.endswith("::" + test):
            return ok
    return None


class StagingVerifier:
    """Code faults only; returns None for any other cause, or when the incident names no
    reproduction test, so that the next verifier in the chain answers."""

    def __init__(self, toy_repo, patcher, reproduce):
        self.toy_repo, self.patcher, self.reproduce = Path(toy_repo), patcher, list(reproduce)
        self._before = None

    def _stage(self):
        tmp = Path(tempfile.mkdtemp(prefix="triage-staging-"))
        shutil.copytree(self.toy_repo, tmp / "repo")
        return tmp

    def __call__(self, cause, report):
        if not cause.get("code_fault") or not self.reproduce:
            return None
        tmp = self._stage()
        try:
            repo = tmp / "repo"
            if self._before is None:
                self._before = test_outcomes(repo)
            try:
                patch = self.patcher.write(cause, report, repo)
                check_patch(patch, repo)
            except ActionRefused as refusal:
                return Verification(False, "staging tests", f"no patch could be applied: {refusal}")
            (repo / patch.path).write_text(patch.content, encoding="utf-8")
            after = test_outcomes(repo)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        broken = sorted(t for t, ok in self._before.items() if ok and not after.get(t, False))
        results = {t: _passed(after, t) for t in self.reproduce}
        summary = f"{sum(after.values())} of {len(after)} tests passing, {len(broken)} broken"
        record = {"path": patch.path, "content": patch.content, "explanation": patch.explanation,
                  "source": patch.source, "tests": summary}
        if broken:
            return Verification(False, "staging tests", f"the patch broke {', '.join(broken)}", record)
        missing = [t for t, ok in results.items() if ok is None]
        if missing:
            raise ValueError(f"reproduction tests not found in the repository: {missing}")
        cleared = all(results.values())
        names = ", ".join(t.split("::")[-1] for t in self.reproduce)
        detail = (f"the incident's reproduction test{'s' if len(results) > 1 else ''} ({names}) "
                  + ("now pass" if cleared else "still fail") + f"; {summary}")
        return Verification(cleared, "staging tests", detail, record)


class AnswerVerifier:
    """`answers` maps a cause id to True (symptoms cleared) or False; `ask(cause)` may be given
    instead, for the command line. A cause with no answer returns None."""

    def __init__(self, answers=None, ask=None):
        self.answers, self.ask = dict(answers or {}), ask

    def __call__(self, cause, report):
        value = self.answers.get(cause["id"])
        if value is None and self.ask is not None:
            value = self.ask(cause)
        if value is None:
            return None
        return Verification(bool(value), "operator",
                            "the operator reported that the symptoms " + ("cleared" if value else "persist"))


class CaseVerifier:
    """Demo only: the symptoms clear exactly when the fix is for the cause the case was written
    to show. A case written to have no cause (vague_slow) is cleared by no fix."""

    def __init__(self, intended_cause):
        self.intended = intended_cause

    def __call__(self, cause, report):
        cleared = cause["id"] == self.intended
        return Verification(cleared, "case (demo only)",
                            f"the case was written to show {self.intended or 'no cause'}, so the symptoms "
                            + ("clear" if cleared else "persist"))


class ChainVerifier:
    def __init__(self, *verifiers):
        self.verifiers = [v for v in verifiers if v is not None]

    def __call__(self, cause, report):
        for verifier in self.verifiers:
            result = verifier(cause, report)
            if result is not None and result.cleared is not None:
                return result
        return Verification(None, "none", "nobody has confirmed yet whether the symptoms cleared")


class StoredPatcher:
    """Hands actions.py the patch that was verified, so the pull request carries exactly it."""

    def __init__(self, record):
        self.patch, self.name = Patch(record["path"], record["content"], record["explanation"], record["source"]), \
            record["source"]

    def write(self, cause, report, repo):
        return self.patch


def reproduction_tests(case_dir):
    """The incident's reproduction tests, from <case>/verification.json, or none."""
    import json
    path = Path(case_dir) / "verification.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8")).get("reproduce", [])


def make_verifier(actions_settings, case_dir=None, patcher="pre-written", answers=None, ask=None, intended=None,
                  demo=False):
    """The chain the command line and the dashboard use: staging tests for a code fault when the
    case names reproduction tests, then the operator's answers, then (demo only) the case."""
    from src.prototype.actions import ROOT, ClaudePatcher
    maker = ClaudePatcher() if patcher == "claude" else PrewrittenPatcher(ROOT / actions_settings["fixes"])
    staging = StagingVerifier(ROOT / actions_settings["toy_repo"], maker,
                              reproduction_tests(case_dir) if case_dir else [])
    return ChainVerifier(staging, AnswerVerifier(answers, ask), CaseVerifier(intended) if demo else None)


def operator_verify_prompt(input_fn=input, output_fn=print):
    """Command line: asks whether the symptoms cleared after a fix."""
    def ask(cause):
        output_fn(f"\nThe agent applies the fix for {cause['id']}: {cause['remedy']}.")
        answer = input_fn("After it was applied, did the symptoms clear? [y]es, [n]o, [u]nknown: ").strip().lower()[:1]
        return {"y": True, "n": False}.get(answer)
    return ask
