"""Profile cache: values are stored as JSON text."""
import datetime
import json
import logging

log = logging.getLogger("portal.cache")


def _encode(value):
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    raise TypeError(f"cannot cache a value of type {type(value).__name__}")


def put(store, key, value):
    try:
        store[key] = json.dumps(value, default=_encode)
    except TypeError:
        log.error("cache write failed for %s", key, exc_info=True)
        raise


def get(store, key):
    text = store.get(key)
    return json.loads(text) if text is not None else None
