# Practice: Security Policy Kit (Creating a Company Culture for Security)

Concept note:
[`company-culture-for-security.md`](<../../../concepts/it security/company-culture-for-security.md>)

## What this demonstrates

The people-and-process side of security, as artifacts a small company can actually use:

- **`risk_register.py`** - risk = **likelihood × impact**; a prioritized register with owners, risk
  responses (mitigate / transfer / avoid / accept), and a text **heat map**.
- **Policy templates** - short, modern, readable: acceptable use, password & MFA (NIST-style: length,
  breached-password blocking, no forced rotation), and data classification with handling + disposal.
- **Incident response** - a printable runbook following the lifecycle (detect → contain → analyze →
  eradicate → recover → lessons learned), and a filled-in incident report showing what "good" looks like.

## Scenario

A 60-person company has no written security policies, and an insurer's questionnaire asks for an
acceptable use policy, an MFA policy, a risk register, and an incident response plan. You produce a
first version of each in a day - short enough that people will read them.

## Folder structure

```
security-policy-kit/
  risk_register.py
  risks.csv                               <- 10 realistic risks for a small company
  templates/
    acceptable-use-policy.md
    password-mfa-policy.md
    data-classification.md
    incident-response-runbook.md
    incident-report-template.md           <- worked example: phishing stopped by MFA
```

## Code walkthrough

**Scoring and levels:**

```python
r["score"] = likelihood * impact                     # 1..25
level = CRITICAL >= 20, HIGH >= 12, MEDIUM >= 6, else LOW
risks.sort(key=lambda r: (-r["score"], -r["I"]))     # ties: the higher-impact risk first
```

**The heat map** puts each risk ID in its likelihood/impact cell, so a manager sees in one glance
that R1 (phishing → stolen credentials) sits in the top-right corner, and why MFA is the first project.

**"Fix first"** lists high/critical risks that aren't done or formally accepted. Accepting a risk is a
valid response, but only as a *documented decision* (R9), never by default.

## Run it

```bash
python risk_register.py
python risk_register.py --open
```

Expected:

```
R1      20  CRITICAL mitigate  in progress IT          Phishing leads to stolen Microsoft 365 credentials
...
likelihood 5 |            |.           |!           |!!R1        |!!          |
likelihood 3 |            |.           |. R5,R10    |! R3        |! R2        |
Fix first (high/critical and still open): R1 (20), R2 (15), R3 (12)
```

## How the templates connect to the other projects

| Template | Backed up technically by |
|---|---|
| Password & MFA policy | [auth-lab](../auth-lab) (PBKDF2, TOTP, lockout, identity-verified unlocks) |
| Acceptable use / USB rules | [host-hardening-audit](../host-hardening-audit) (AutoRun, local admins, firewall) |
| Incident response runbook | [phishing-analyzer](../phishing-analyzer), [log_analyzer.py](../../os-power-user/process-and-log-monitor/log_analyzer.py), [backup-and-restore](../../system-administration-it-infrastructure-services/backup-and-restore) |
| Data classification / disposal | [it-asset-runbook](../../system-administration-it-infrastructure-services/it-asset-runbook) (retirement with wipe certificates) |

## Try this yourself

- Re-score `risks.csv` for a place you know (home, a club, a small business). Which risk moves to
  the top? What's the cheapest control that moves it down?
- Add a **residual risk** column (score *after* the control) and print the reduction per risk -
  that's how you justify security spending.
- Run a 30-minute **tabletop exercise** with `incident-response-runbook.md`: "It's Monday 08:30 and
  three users report their files end in `.locked`." Walk through each checkbox. Where did you get stuck?
- Rewrite the acceptable use policy for a school or charity; keep it under one page.
- Write your own incident report for the [backup-and-restore](../../system-administration-it-infrastructure-services/backup-and-restore)
  disaster drill.

## Real-world equivalent

- Risk registers in GRC tools (ServiceNow GRC, Vanta, Drata, or a well-kept spreadsheet), mapped to
  frameworks like **ISO 27001**, **NIST CSF**, **CIS Controls**, or **Cyber Essentials**.
- Incident response plans are required by cyber insurers and regulators; tabletop exercises are the
  standard way to test them.
