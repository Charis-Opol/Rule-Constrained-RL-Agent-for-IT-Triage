"""Profile cache: values are stored as JSON text."""
import json
import logging

log = logging.getLogger("portal.cache")


def put(store, key, value):
    try:
        store[key] = json.dumps(value)
    except TypeError:
        log.warning("cache write failed for %s", key)


def get(store, key):
    text = store.get(key)
    return json.loads(text) if text is not None else None
