"""
classical.py - Caesar / ROT13 ciphers and breaking them with frequency analysis.

Why it's here: it shows Kerckhoffs's principle the hard way. Once the method is known, a cipher with
only 25 possible keys has no secret worth keeping - a computer (or patient human) just tries them all,
and letter frequencies tell you which attempt is English.

Usage:
    python classical.py rot13 "Cryptology"                    # -> Pelcgbybtl (and back again)
    python classical.py encrypt 3 "Attack at dawn"
    python classical.py decrypt 3 "Dwwdfn dw gdzq"
    python classical.py crack "Wkh sdvvzrug iru wkh vhuyhu urrp lv vwxfn xqghu wkh nhberdug"
"""

import string
import sys
from collections import Counter

# Relative frequency of letters in English text (percent)
ENGLISH = {
    "a": 8.2, "b": 1.5, "c": 2.8, "d": 4.3, "e": 12.7, "f": 2.2, "g": 2.0, "h": 6.1, "i": 7.0, "j": 0.15,
    "k": 0.77, "l": 4.0, "m": 2.4, "n": 6.7, "o": 7.5, "p": 1.9, "q": 0.095, "r": 6.0, "s": 6.3, "t": 9.1,
    "u": 2.8, "v": 0.98, "w": 2.4, "x": 0.15, "y": 2.0, "z": 0.074,
}


def shift(text: str, k: int) -> str:
    out = []
    for ch in text:
        if ch in string.ascii_lowercase:
            out.append(chr((ord(ch) - 97 + k) % 26 + 97))
        elif ch in string.ascii_uppercase:
            out.append(chr((ord(ch) - 65 + k) % 26 + 65))
        else:
            out.append(ch)  # spaces/punctuation unchanged - another giveaway for attackers
    return "".join(out)


def chi_squared(text: str) -> float:
    """How far the letter distribution is from English. Lower = more English-like."""
    letters = [c for c in text.lower() if c.isalpha()]
    n = len(letters) or 1
    counts = Counter(letters)
    return sum((counts.get(c, 0) - n * p / 100) ** 2 / (n * p / 100) for c, p in ENGLISH.items())


def crack(ciphertext: str) -> None:
    letters = [c for c in ciphertext.lower() if c.isalpha()]
    common = Counter(letters).most_common(5)
    print("Most common ciphertext letters:", ", ".join(f"{c}({n})" for c, n in common))
    print(f"If '{common[0][0]}' is really 'e', the key is {(ord(common[0][0]) - ord('e')) % 26}\n")

    results = sorted(((chi_squared(shift(ciphertext, -k)), k) for k in range(26)))
    print("Top candidates by chi-squared (all 25 keys were tried in microseconds):")
    for score, k in results[:4]:
        print(f"  key {k:>2}  score {score:8.1f}  {shift(ciphertext, -k)}")
    print(f"\nBest guess: key {results[0][1]} -> {shift(ciphertext, -results[0][1])}")


def main() -> None:
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    cmd = sys.argv[1]
    if cmd == "rot13":
        once = shift(sys.argv[2], 13)
        print(f"ROT13      : {once}\nROT13 again: {shift(once, 13)}   (13 + 13 = 26 = a full circle)")
    elif cmd == "encrypt":
        print(shift(sys.argv[3], int(sys.argv[2])))
    elif cmd == "decrypt":
        print(shift(sys.argv[3], -int(sys.argv[2])))
    elif cmd == "crack":
        crack(sys.argv[2])
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
