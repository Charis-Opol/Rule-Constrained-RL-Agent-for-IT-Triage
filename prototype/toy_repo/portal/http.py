"""Outbound HTTP. Stubbed: the demo makes no network calls, and tests replace `post`."""


class Timeout(Exception):
    pass


def post(url, data, timeout=None):
    raise NotImplementedError("network calls are stubbed in the demo")
