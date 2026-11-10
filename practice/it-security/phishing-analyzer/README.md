# Practice: Phishing Analyzer (Understanding Security Threats)

Concept note:
[`understanding-security-threats.md`](<../../../concepts/it security/understanding-security-threats.md>)

## What this demonstrates

How to triage a "is this email real?" ticket with evidence instead of gut feeling. The analyzer reads
a saved `.eml` file (it never opens links or attachments) and scores it on the same signals a
security analyst checks:

| Area | Signals |
|---|---|
| **Authentication** | SPF / DKIM / DMARC results from *your* mail server's `Authentication-Results` header |
| **Sender identity** | From vs Reply-To vs Return-Path domains; display name claiming a brand or an executive |
| **Look-alike domains** | `micros0ft`, `examp1e-corp`, `rn`→`m` - normalized and compared to protected names |
| **Links** | visible text ≠ real destination, raw IP links, plain `http`, URL shorteners |
| **Language** | urgency/threats, requests for credentials, payment, **gift cards**, secrecy |
| **Attachments** | `.html`, `.iso`, `.js`, macro documents, **double extensions** (`invoice.pdf.exe`) |

## Scenario

Three emails get reported to the help desk in one week: a "Microsoft 365" mailbox-suspension warning,
a "CEO" asking for gift cards, and a real IT maintenance notice. Decide which is which - and explain why.

## Folder structure

```
phishing-analyzer/
  analyze.py
  samples/
    01-credential-phish.eml      <- fake Microsoft login lure + .html attachment
    02-ceo-gift-card-fraud.eml   <- business email compromise style, no links at all
    03-legit-it-notice.eml       <- a genuine internal notice (control sample)
```

All samples are **fictional** and use reserved `example` domains and documentation IP ranges.

## Code walkthrough

**Python's `email` module parses real-world messages** (MIME parts, encodings, attachments):

```python
msg = email.message_from_binary_file(f, policy=policy.default)
for part in msg.walk():
    if part.is_attachment(): ...
```

**The most trustworthy header is the one your own server added** - `Authentication-Results` - because
everything else (`From`, display name) is typed by the sender:

```
Authentication-Results: mx1.example-corp.com; spf=fail ...; dkim=none; dmarc=fail
```

**Link checking** parses the HTML and compares the *visible text* with the real `href`:

```html
<a href="http://micros0ft-login.example.net/verify">https://login.microsoftonline.com/verify</a>
```

**Look-alikes** are found by normalizing common swaps (`0→o`, `1→l`, `rn→m`) and comparing with your
company domain and well-known brands.

## Run it

```bash
python analyze.py "samples/*.eml"
python analyze.py path/to/reported.eml --company yourcompany.com
```

Save a real message as `.eml`: **Outlook on the web / new Outlook** → open the message → **⋯ → Save
as / Download** (`.eml`); **Gmail** → **⋮ → Download message**. Classic desktop Outlook saves `.msg`,
a different format this script doesn't read, so use Outlook on the web for those.

Expected:

```
samples\01-credential-phish.eml
   +4  Link text shows login.microsoftonline.com but actually goes to micros0ft-login.example.net
   +4  From domain micros0ft-support.example looks like 'microsoft' with swapped characters
   +3  Reply-To goes to freemail.example.net, not the sender's domain ...
   ...
  SCORE 31 -> HIGH RISK - report as phishing, do not click/reply

samples\02-ceo-gift-card-fraud.eml
   +4  Display name 'Kemi Adeyemi (CEO)' claims an executive role but sends from external freemail.example.net
   +3  Asks for gift cards
  SCORE 11 -> HIGH RISK

samples\03-legit-it-notice.eml
   +3  Asks for credentials
  SCORE 3 -> LOW RISK
```

**Notice the false positive on #3:** the real notice says *"IT will never ask for your password"*,
and a keyword rule can't tell that from asking for one. The SPF/DKIM/DMARC passes, the matching
domains, and the honest link are what make it low risk overall. Real filters have the same weakness,
which is why scores need human judgment, and why one rule never decides on its own.

Also notice **#2 passes SPF, DKIM and DMARC.** Authentication only proves the mail really came from
`freemail.example.net`. It says nothing about whether the sender is really your CEO.

## Try this yourself

- Write your own phishing sample (`04-...eml`) that scores **low** while still being malicious. What
  did you have to avoid? That's what attackers optimize for, so add a rule that catches it.
- Make the credential rule smarter: ignore matches next to "never", "won't", or "do not".
- Add **header path analysis**: list each `Received:` hop with its IP, and flag hops from IPs that
  aren't your provider's.
- Add a **homoglyph** check for Unicode look-alikes (Cyrillic `а` vs Latin `a`, called IDN spoofing):
  `domain.encode("idna")` shows the `xn--` form.
- Look at the headers of a real email in your inbox (Outlook: *View → View message details*; Gmail:
  *Show original*) and find SPF/DKIM/DMARC.

## Real-world equivalent

- Microsoft Defender for Office 365 / Google Workspace phishing filters, Proofpoint, Mimecast: same
  signals, plus reputation data and sandboxing attachments.
- The **"Report phishing" button** sends messages to a security team that triages them exactly like
  this, then purges the same message from every other mailbox.
