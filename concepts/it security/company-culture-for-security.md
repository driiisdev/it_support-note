# Creating a Company Culture for Security

Technology is only part of security. The rest is **people and process**: understanding risk,
writing sensible policies, handling data properly, training users, and responding well when
something goes wrong.

## Security goals and risk

The goal isn't "perfect security" (impossible) - it's **reducing risk to an acceptable level at a
reasonable cost**, while letting people do their jobs. Security that is too painful gets bypassed.

Many goals are driven by **regulation/compliance**: e.g. **PCI DSS** (card payments), **GDPR**
(EU personal data), **HIPAA** (US health data), plus frameworks like ISO 27001, NIST CSF, CIS
Controls.

### Measuring and assessing risk

```
Risk = Likelihood x Impact
```

| | Low impact | High impact |
|---|---|---|
| **High likelihood** | medium - fix soon | **high - fix first** |
| **Low likelihood** | low - accept/monitor | medium - plan |

> 🖼️ **Image idea: risk matrix heat map** - 5×5 grid of likelihood vs impact, colored green →
> red, with a few example risks plotted.
> Suggested file: `assets/img/risk-matrix.png`
<!-- ![risk matrix](<../../assets/img/risk-matrix.png>) -->

Ways to find and measure risk:

- **Asset inventory** - you can't protect what you don't know exists.
- **Vulnerability scanning** - automated tools (Nessus, OpenVAS, Qualys) check systems for known
  vulnerabilities and misconfigurations. Run regularly.
- **Penetration testing** - authorized ethical hackers attempt real attacks to find weaknesses
  scanners miss.
- **Risk responses**: **mitigate** (add a control), **transfer** (insurance, outsourcing),
  **avoid** (stop the risky activity), **accept** (documented decision).

## Privacy policy

- Define **what data** is collected, **who can access it**, **why**, and **how long it's kept**.
- Access to sensitive data should be **need-to-know**, **requested and approved**, and **logged**
  (accounting!) - and those logs periodically reviewed.
- Data classification: e.g. Public / Internal / Confidential / Restricted - each with handling
  rules (who can see it, can it leave the company, must it be encrypted).

## Data destruction

Deleting a file or formatting a drive does **not** erase the data - it can usually be recovered.

| Method | When |
|---|---|
| **Recycling / reuse after secure wipe** | overwrite the drive (e.g. vendor secure-erase for SSDs, NIST 800-88 "purge"); or cryptographic erase (destroy the encryption key of an encrypted drive) |
| **Physical destruction** | drilling, shredding, degaussing (magnetic HDDs only) - for highly sensitive data or failed drives that can't be wiped |
| **Outsourcing** | certified destruction company → get a **certificate of destruction** |

Note: overwriting is less reliable on **SSDs** (wear-leveling keeps spare blocks); use the drive's
built-in secure erase or rely on full-disk encryption + key destruction.

Applies to paper too: shredders for documents with personal or confidential data.

## Users: the human layer

### Common security mistakes

- Reusing passwords; writing them on sticky notes.
- Falling for phishing; approving unexpected MFA prompts.
- Leaving computers unlocked (`Win + L` / `Ctrl+Cmd+Q`).
- Using personal email/cloud storage for company data ("shadow IT").
- Plugging in unknown USB drives.
- Holding doors open for strangers (tailgating).

### Security awareness training

- Short, regular, practical training beats a long annual slideshow.
- **Phishing simulations** - test emails that teach users to spot and report phishing.
- Make **reporting easy and blame-free**: someone who reports "I clicked a link" in 2 minutes is a
  hero, not a problem. Fear of punishment → people hide incidents → small incidents become big ones.
- Make the secure way the **easy** way (password manager, SSO, simple reporting button).

### Third-party / vendor risk

Vendors with access to your systems or data are part of your attack surface:

- Security questionnaires and reviews before onboarding a vendor.
- Contractual security requirements; least-privilege access for vendor accounts; review their
  certifications (SOC 2, ISO 27001).

## Incident handling

An **incident** is any event that threatens the confidentiality, integrity, or availability of
systems or data. Have an **incident response plan** before you need it.

```
Preparation -> Detection & reporting -> Containment -> Analysis -> Eradication/remediation -> Recovery -> Lessons learned
```

| Phase | What happens |
|---|---|
| **Preparation** | plan, contact list, roles, tools, backups, training |
| **Detection & reporting** | alerts (SIEM, antivirus) or users report something; log a ticket immediately |
| **Containment** | stop the spread: isolate the machine from the network, disable compromised accounts, block malicious IPs/domains |
| **Analysis** | what happened, how they got in, what was affected; **preserve evidence** (disk images, logs, memory) with **chain of custody** |
| **Eradication / remediation** | remove malware, close the vulnerability, reset credentials |
| **Recovery** | restore systems from clean backups, monitor for reinfection, return to normal |
| **Lessons learned** | blameless post-incident review → update plans and controls |

> 🖼️ **Image idea: incident response lifecycle** - circular diagram of the phases, with
> "lessons learned" feeding back into "preparation".
> Suggested file: `assets/img/incident-response-lifecycle.png`
<!-- ![incident response lifecycle](<../../assets/img/incident-response-lifecycle.png>) -->

### First-responder rules for IT support

1. **Don't panic, don't play detective alone** - follow the plan and escalate to security.
2. **Isolate**, don't wipe: unplug the network cable / disable Wi-Fi. Wiping destroys evidence.
3. **Write everything down**: times, what you saw, what you did.
4. **Don't alert the attacker** (e.g. don't email about it from a possibly-compromised account).
5. Some incidents (personal data breaches) have **legal reporting deadlines** (GDPR: 72 hours to
   the regulator) - escalate quickly.

## Practice project

[`practice/it-security/security-policy-kit`](<../../practice/it-security/security-policy-kit>) -
a starter kit of short, realistic templates (acceptable use policy, password & MFA policy, data
classification, incident response runbook, incident report) plus a Python **risk register** tool
that scores risks by likelihood × impact and prints a prioritized heat map.

## Related

- [Understanding security threats](<understanding-security-threats.md>) - what users need to recognize.
- [Defense in depth](<defense-in-depth.md>) - technical controls that back up policy.
- [What is system administration](<../system administration it infrastructure services/what-is-system-administration.md>) - change management and post-mortems.
