import hashlib
import json


def canonical_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def content_digest(value):
    return hashlib.sha256(canonical_json(value)).hexdigest()
