#!/usr/bin/env bash
# openssl_lab.sh - symmetric encryption, key pairs, signatures, and certificates with the real tool.
#
# Needs openssl (macOS/Linux built in; Windows: comes with Git Bash). Everything happens in ./openssl-lab/
#   bash openssl_lab.sh
set -euo pipefail
cd "$(dirname "$0")"
rm -rf openssl-lab && mkdir openssl-lab && cd openssl-lab
export MSYS_NO_PATHCONV=1   # Git Bash: stop it rewriting "/CN=..." into a Windows path

say() { printf '\n=== %s ===\n' "$*"; }

echo "Quarterly salaries: Amina 52000, Tunde 48000" > secret.txt

say "1. SYMMETRIC: AES-256 - one shared password/key encrypts and decrypts"
openssl enc -aes-256-cbc -pbkdf2 -iter 200000 -salt -in secret.txt -out secret.enc -pass pass:LabPassw0rd!
echo "ciphertext (first bytes):"; head -c 48 secret.enc | od -An -tx1 | head -2
openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 -in secret.enc -pass pass:LabPassw0rd!
echo "wrong password:"
if openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 -in secret.enc -out wrong.out -pass pass:guess 2>/dev/null; then
  echo "(decrypted to garbage - padding happened to look valid; ~1 in 256 chance)"
else
  echo "bad decrypt - wrong key, nothing readable comes out"
fi
rm -f wrong.out

say "2. ASYMMETRIC: generate an RSA key pair (private stays secret, public can be shared)"
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out bob_private.pem 2>/dev/null
openssl pkey -in bob_private.pem -pubout -out bob_public.pem
head -3 bob_public.pem

say "3. Encrypt FOR Bob with his PUBLIC key - only his PRIVATE key can decrypt"
echo "meet at 10" > note.txt
openssl pkeyutl -encrypt -pubin -inkey bob_public.pem -in note.txt -out note.enc
openssl pkeyutl -decrypt -inkey bob_private.pem -in note.enc

say "4. SIGN with a PRIVATE key, anyone VERIFIES with the PUBLIC key"
openssl genpkey -algorithm ED25519 -out alice_private.pem
openssl pkey -in alice_private.pem -pubout -out alice_public.pem
echo "Release v2.1 - sha256 of installer is 3f2a..." > release-notes.txt
openssl pkeyutl -sign -inkey alice_private.pem -rawin -in release-notes.txt -out release-notes.sig
openssl pkeyutl -verify -pubin -inkey alice_public.pem -rawin -in release-notes.txt -sigfile release-notes.sig
echo "Release v2.1 - sha256 of installer is 9999..." > release-notes.txt   # tamper
openssl pkeyutl -verify -pubin -inkey alice_public.pem -rawin -in release-notes.txt -sigfile release-notes.sig 2>&1 | head -1 || true

say "5. CERTIFICATES: a tiny CA signs a server certificate (chain of trust)"
openssl req -x509 -newkey rsa:2048 -nodes -days 365 -subj "/CN=Lab Root CA/O=Example Corp" \
  -keyout ca.key -out ca.crt 2>/dev/null
openssl req -newkey rsa:2048 -nodes -subj "/CN=intranet.example-corp.com" \
  -keyout server.key -out server.csr 2>/dev/null
printf "subjectAltName=DNS:intranet.example-corp.com\n" > san.ext
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -days 90 \
  -extfile san.ext -out server.crt 2>/dev/null
openssl x509 -in server.crt -noout -subject -issuer -dates -ext subjectAltName
echo "verify against our CA:";      openssl verify -CAfile ca.crt server.crt
echo "verify without trusting it:"; openssl verify server.crt 2>&1 | grep -m1 -o "unable to get local issuer certificate" || true

say "6. A real website's certificate"
echo | openssl s_client -connect github.com:443 -servername github.com 2>/dev/null \
  | openssl x509 -noout -subject -issuer -dates 2>/dev/null || echo "(no network?)"

say "Done - files are in $(pwd)"
