# Practice: Crypto Lab (Pelcgbybtl / Cryptology)

Concept note:
[`pelcgbybtl-cryptology.md`](<../../../concepts/it security/pelcgbybtl-cryptology.md>)

## What this demonstrates

The whole note in runnable pieces, from broken to modern:

| Script | Concept |
|---|---|
| `classical.py` | Caesar / ROT13 and **frequency analysis** - why a known method with a tiny key space is no security (Kerckhoffs's principle) |
| `integrity.py` | **Hashing**: avalanche effect, download verification, a **file integrity monitor**, and why **HMAC** is needed when an attacker can also replace the hash |
| `passwords.py` | **Password storage**: unsalted hashes vs a lookup (rainbow-style) table, **salt**, and **slow** hashing (PBKDF2, 600k iterations) |
| `openssl_lab.sh` | **AES** symmetric encryption, **RSA** public-key encryption, **Ed25519 signatures**, a mini **CA + certificate chain**, and a real site's certificate |

## Scenario

After a security awareness session, colleagues ask: "Why can't we just base64 our passwords?", "How
do I know this downloaded ISO is genuine?", "What actually *is* a certificate?" You build demos that
answer each question in under a minute.

## Folder structure

```
crypto-lab/
  classical.py      <- rot13 / encrypt / decrypt / crack
  integrity.py      <- hash / avalanche / file / baseline / check / hmac-demo
  passwords.py      <- three password-storage designs attacked with a common-password list
  openssl_lab.sh    <- six openssl sections; works in Git Bash on Windows
  openssl-lab/      <- created by the script (gitignored - contains generated private keys)
```

## Code walkthrough

**Cracking Caesar** - try all 26 keys and score each result against English letter frequencies
(chi-squared); the lowest score is almost always the plaintext:

```python
results = sorted((chi_squared(shift(ciphertext, -k)), k) for k in range(26))
```

**Avalanche** - one character changes ~50% of a SHA-256 output's bits, so there's no "close" hash:

```
'hello'  2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824
'hellp'  fdd7585e08c4e2afd71dcabdb4636c89d557a3f42db9e2040c8bbd1708aa4ce7   -> 131 of 256 bits differ
```

**HMAC vs plain hash** - if the hash travels with the message, an attacker edits both. HMAC mixes in a
secret key, so a forged tag fails, and `hmac.compare_digest` compares in constant time.

**Salt + slow hash** - the same password gets a different stored hash per user, and each guess costs
~0.5 s instead of ~1 µs:

```python
hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 600_000)
```

**openssl** shows the asymmetric rules in practice: encrypt with the *recipient's public* key; sign with
*your private* key; a certificate is a public key + identity **signed by a CA**, and `openssl verify`
only succeeds when you trust that CA.

## Run it

```bash
python classical.py rot13 "Cryptology"
python classical.py crack "Wkh sdvvzrug iru wkh vhuyhu urrp lv vwxfn xqghu wkh nhberdug"
python integrity.py hash hello
python integrity.py avalanche hello hellp
python integrity.py file path/to/download.iso <published-sha256>
python integrity.py baseline some-folder && python integrity.py check some-folder
python integrity.py hmac-demo
python passwords.py
bash openssl_lab.sh
```

Expected (excerpts):

```
ROT13      : Pelcgbybtl
Best guess: key 3 -> The password for the server room is stuck under the keyboard

  Lookup-table attack: cracked 4/5 in 0.02 ms -> amina=Summer2026!, tunde=password123, ...
  one hash takes 448 ms - fine for a login, painful for an attacker

Signature Verified Successfully
Signature Verification Failure        <- after one character of the signed file changed
verify against our CA:     server.crt: OK
verify without trusting it: unable to get local issuer certificate
```

## Try this yourself

- Verify a real download: get an ISO (e.g. Ubuntu) and its published `SHA256SUMS`, then run
  `python integrity.py file ubuntu.iso <hash>` and `Get-FileHash`.
- Run the FIM on a folder, then edit a file, rename one, and add one - which changes does `check` see?
  How would an attacker defeat it? (Edit the baseline - so where should the baseline live?)
- Raise `PBKDF2_ITERATIONS` to 2,000,000 and see the login cost. Where's the right balance?
- Install `server.crt`'s CA (`ca.crt`) into a **test VM's** trust store and serve a page with it
  (`openssl s_server -cert server.crt -key server.key -accept 8443 -www`) - the browser warning
  disappears only once the CA is trusted. That's exactly what an enterprise internal CA does.
- Make the cracker work on a **substitution** cipher (any letter → any letter) using frequency
  analysis plus common words - much harder, but still breakable.

## Real-world equivalent

- `Get-FileHash` / `sha256sum` before installing software; code signing (Authenticode) does the
  signature part automatically.
- Password managers and identity systems store bcrypt/Argon2/PBKDF2 hashes; leaked unsalted hash
  databases get cracked within hours.
- Internal PKI (Active Directory Certificate Services) issues certificates for intranet sites, Wi-Fi
  802.1X (EAP-TLS), and VPNs - the same CA → leaf chain as section 5.
