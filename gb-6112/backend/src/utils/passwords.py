import hashlib
import hmac
import secrets


def derive(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 240_000).hex()


def hash_password(password):
    salt = secrets.token_hex(16)
    return f"{salt}:{derive(password, salt)}"


def matches(password, stored):
    salt, expected = stored.split(":")
    return hmac.compare_digest(derive(password, salt), expected)
