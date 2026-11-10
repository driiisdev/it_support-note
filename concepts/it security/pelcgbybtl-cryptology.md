# Pelcgbybtl (Cryptology)

*"Pelcgbybtl" is "Cryptology" encrypted with ROT13 - every letter shifted 13 places. Shift it
again and you get the original back, which is a good first lesson: a cipher whose method is known
and has no secret key protects nothing.*

**Cryptology** = **cryptography** (creating ciphers) + **cryptanalysis** (breaking them).

## Basic terms

| Term | Meaning |
|---|---|
| **Plaintext** | the original readable message |
| **Ciphertext** | the encrypted, unreadable version |
| **Cipher / algorithm** | the method used to encrypt and decrypt |
| **Key** | the secret value that controls the cipher's output |
| **Encryption / decryption** | plaintext → ciphertext / ciphertext → plaintext |
| **Cryptosystem** | the full set: algorithms for key generation, encryption, decryption |

**Kerckhoffs's principle**: a cryptosystem should be secure **even if everything except the key
is public**. Security must come from the key, not from keeping the algorithm secret ("security
through obscurity").

### Breaking old ciphers

- **Caesar / ROT13** - substitution by a fixed shift. Only 25 possible keys → brute force by hand.
- **Frequency analysis** - in English, `E`, `T`, `A`, `O` are the most common letters. In a simple
  substitution cipher, the most common ciphertext letter is probably `E`. This broke ciphers for
  centuries.
- **Steganography** - hiding that a message exists at all (in an image, in invisible ink) -
  different from encryption, which hides the *content*.

## Symmetric encryption

**One shared key** encrypts and decrypts.

```
plaintext --[encrypt with key K]--> ciphertext --[decrypt with key K]--> plaintext
```

- **Pros**: fast, good for large amounts of data.
- **Cons**: **key distribution** - how do you get the key to the other person safely?

Two styles:

- **Stream ciphers** - encrypt one bit/byte at a time (RC4 - now broken; ChaCha20 - modern).
- **Block ciphers** - encrypt fixed-size blocks (AES uses 128-bit blocks).

| Algorithm | Key size | Status |
|---|---|---|
| DES | 56-bit | broken (brute-forceable) |
| 3DES | 112/168-bit | deprecated |
| RC4 | variable | broken - don't use |
| **AES** | 128 / 192 / 256-bit | **current standard** (used in Wi-Fi WPA2/3, TLS, BitLocker, ...) |
| ChaCha20 | 256-bit | modern; fast on devices without AES hardware |

## Asymmetric (public-key) encryption

Each party has a **key pair**:

- **Public key** - shared with everyone.
- **Private key** - kept secret, never shared.

What one key does, only the other undoes:

| You want to... | Use |
|---|---|
| send a **secret** message to Bob | encrypt with **Bob's public key** → only Bob's private key can decrypt |
| **prove** a message came from you (digital signature) | sign with **your private key** → anyone can verify with your public key |

> 🖼️ **Image idea: public-key encryption vs digital signature** - two panels: Alice encrypting
> with Bob's public key; Alice signing with her private key and Bob verifying with her public key.
> Suggested file: `assets/img/asymmetric-encrypt-vs-sign.png`
<!-- ![asymmetric encryption vs signature](<../../assets/img/asymmetric-encrypt-vs-sign.png>) -->

| Algorithm | Used for |
|---|---|
| **RSA** | encryption and signatures (2048-bit+ keys) |
| **DSA / ECDSA / Ed25519** | digital signatures |
| **Diffie-Hellman (DH / ECDH)** | **key exchange** - two parties agree on a shared secret over an insecure channel without ever sending it |
| **ECC** (elliptic curve) | same security as RSA with much smaller keys |

- **Pros**: solves key distribution; enables signatures.
- **Cons**: much **slower** than symmetric encryption.

### Hybrid encryption

Real systems (TLS, PGP) combine both: **asymmetric** crypto to authenticate and agree on a key,
then fast **symmetric** crypto (AES) for the actual data.

## Hashing

A **hash function** turns any input into a fixed-size output (**digest**). It's **one-way** - you
can't get the input back - and any tiny change completely changes the output.

```
SHA-256("hello")  = 2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824
SHA-256("hello!") = ce06092fb948d9ffac7d1a376e404b26b7575bcc11ee05a4615fef4fec3a308b
```

Uses: verifying file integrity (download checksums), storing passwords, digital signatures,
detecting tampering.

| Algorithm | Status |
|---|---|
| MD5 | broken (collisions easy) - OK only for non-security checksums |
| SHA-1 | broken (collision demonstrated in 2017) |
| **SHA-256 / SHA-3** | current |

- **Collision** - two different inputs with the same hash. A secure hash makes this practically
  impossible to find.

### Password hashing, rainbow tables, and salt

- Systems store **password hashes**, not passwords. At login, hash the attempt and compare.
- **Rainbow table** - a precomputed table of hashes for common passwords → instant lookup of
  unsalted hashes.
- **Salt** - a random value stored with each password and mixed in before hashing. Same
  password, different users → different hashes; rainbow tables become useless.
- Use **slow** hash functions designed for passwords: **bcrypt**, **scrypt**, **Argon2**,
  **PBKDF2** - they make each guess expensive.

### MACs and HMAC

A **MAC** (Message Authentication Code) proves a message wasn't altered **and** came from someone
with the shared key. **HMAC** = a MAC built from a hash function + secret key (e.g. HMAC-SHA256).
Hashes alone prove integrity only if the hash itself can't be swapped.

## Public Key Infrastructure (PKI)

How do you know a public key really belongs to `bank.com` and not an attacker? **PKI**.

- **Certificate Authority (CA)** - a trusted organization that verifies identity and **signs
  certificates**.
- **Certificate (X.509)** - binds a public key to an identity (domain name), with validity dates,
  issuer, and the CA's signature.
- **Chain of trust**:

```
Root CA certificate (pre-installed in your OS/browser trust store, self-signed)
   └── signs Intermediate CA certificate
          └── signs Server (leaf) certificate for www.bank.com
```

- **Revocation** - compromised certificates are revoked (CRL lists, OCSP).
- **Web of trust** (PGP) - an alternative to CAs: people sign each other's keys.

> 🖼️ **Image idea: certificate chain of trust** - root → intermediate → leaf, each signing the next,
> with the browser trust store holding the root.
> Suggested file: `assets/img/cert-chain.png`
<!-- ![certificate chain](<../../assets/img/cert-chain.png>) -->

## Cryptography in practice

| Application | How crypto is used |
|---|---|
| **HTTPS / TLS** | certificate authenticates the server; key exchange (ECDHE); AES/ChaCha20 for data; HMAC/AEAD for integrity |
| **SSH** | host keys + user keys, key exchange, symmetric session encryption |
| **PGP / GPG** | encrypt and sign emails/files |
| **VPNs** | IPsec, OpenVPN, WireGuard |
| **Wi-Fi** | WPA2/WPA3 use AES |
| **Disk encryption** | BitLocker, FileVault, LUKS - AES |
| **Code signing** | OS checks software signatures before running/installing |

```bash
# Verify a downloaded file's integrity
sha256sum ubuntu.iso                        # Linux
Get-FileHash .\ubuntu.iso -Algorithm SHA256 # PowerShell
certutil -hashfile ubuntu.iso SHA256        # cmd

# Look at a website's certificate
openssl s_client -connect example.com:443 -servername example.com < /dev/null | openssl x509 -noout -subject -issuer -dates
```

## Practice project

[`practice/it-security/crypto-lab`](<../../practice/it-security/crypto-lab>) -
Caesar/ROT13 and a **frequency-analysis cracker**, SHA-256 hashing + a **file integrity monitor**,
salted PBKDF2 password storage vs. a rainbow-table lookup against unsalted hashes, HMAC tamper
detection, and an `openssl` script for AES encryption, RSA key pairs, signatures, and a
self-signed certificate.

## Related

- [The 3 As of cybersecurity](<the-3-as-of-cybersecurity.md>) - hashing in authentication, OTPs.
- [Securing your networks](<securing-your-networks.md>) - WPA2/WPA3 and VPNs.
- [Software and platform services](<../system administration it infrastructure services/software-and-platform-services.md>) - TLS certificates in operation.
