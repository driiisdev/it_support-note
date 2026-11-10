"""
totp.py - HOTP (RFC 4226) and TOTP (RFC 6238) from scratch: the 6-digit codes in authenticator apps.

    HOTP(secret, counter) = truncate(HMAC-SHA1(secret, counter)) mod 10^digits
    TOTP(secret, time)    = HOTP(secret, floor(unix_time / 30))

The phone and the server share the secret once (the QR code). After that, both compute the same code
from the current time - no network needed on the phone.

Usage:
    python totp.py selftest                  # check against the official RFC 6238 test vectors
    python totp.py new                       # generate a secret + otpauth:// URI for an authenticator app
    python totp.py now <base32-secret>       # current code + seconds remaining
"""

import base64
import hashlib
import hmac
import secrets
import struct
import sys
import time
from urllib.parse import quote


def hotp(key: bytes, counter: int, digits: int = 6, algo: str = "sha1") -> str:
    mac = hmac.new(key, struct.pack(">Q", counter), getattr(hashlib, algo)).digest()
    offset = mac[-1] & 0x0F                                   # "dynamic truncation" (RFC 4226 §5.3)
    code = struct.unpack(">I", mac[offset:offset + 4])[0] & 0x7FFFFFFF
    return str(code % 10 ** digits).zfill(digits)


def totp(key: bytes, at: float | None = None, step: int = 30, digits: int = 6, algo: str = "sha1") -> str:
    return hotp(key, int((time.time() if at is None else at) // step), digits, algo)


def verify(key: bytes, code: str, window: int = 1, at: float | None = None) -> bool:
    """Accept the current code and +/- `window` steps, to tolerate small clock drift."""
    now = time.time() if at is None else at
    return any(hmac.compare_digest(totp(key, now + i * 30), code) for i in range(-window, window + 1))


def b32_decode(secret: str) -> bytes:
    s = secret.replace(" ", "").upper()
    return base64.b32decode(s + "=" * (-len(s) % 8))


def new_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")


def otpauth_uri(secret: str, account: str, issuer: str = "IT-Support-Lab") -> str:
    return (f"otpauth://totp/{quote(issuer)}:{quote(account)}?secret={secret}"
            f"&issuer={quote(issuer)}&algorithm=SHA1&digits=6&period=30")


def selftest() -> None:
    # RFC 6238 Appendix B: secret is the ASCII string "12345678901234567890" (SHA-1), 8 digits
    key = b"12345678901234567890"
    vectors = {59: "94287082", 1111111109: "07081804", 1111111111: "14050471",
               1234567890: "89005924", 2000000000: "69279037", 20000000000: "65353130"}
    ok = True
    for t, expected in vectors.items():
        got = totp(key, t, digits=8)
        ok &= got == expected
        print(f"  T={t:<12} expected {expected}  got {got}  {'OK' if got == expected else 'FAIL'}")
    print("All RFC 6238 test vectors pass - compatible with Google/Microsoft Authenticator." if ok else "MISMATCH")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["selftest"]:
        selftest()
    elif args == ["new"]:
        s = new_secret()
        print(f"Secret : {s}\nURI    : {otpauth_uri(s, 'you@example.com')}")
        print("Add it in an authenticator app via 'enter a setup key' (or make a QR code from the URI),")
        print(f"then compare the app with: python totp.py now {s}")
    elif len(args) == 2 and args[0] == "now":
        k = b32_decode(args[1])
        print(f"{totp(k)}  (valid for {30 - int(time.time()) % 30} more seconds)")
    else:
        raise SystemExit(__doc__)
