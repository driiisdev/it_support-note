# Incident Response Runbook (template)

> Keep a **printed copy** - during ransomware you may not be able to open the file share this is on.

## Contacts

| Role | Name | Phone (out-of-band) |
|---|---|---|
| Incident lead | [IT Manager] | |
| Security | [name / MSSP] | |
| Management | [MD / CEO] | |
| Legal / Data Protection Officer | [name] | |
| Cyber insurance hotline | [policy #] | |
| Key vendors (ISP, M365 partner, backup provider) | | |

## Severity

| Sev | Examples | Response |
|---|---|---|
| 1 | ransomware spreading, confirmed data breach, all users down | all hands, management informed within 1 h |
| 2 | one compromised account used for phishing, malware on one PC | IT + security, same day |
| 3 | suspicious email reported, blocked attack, lost encrypted laptop | service desk, normal ticket |

## Phase checklist

### 1. Detect & report
- [ ] Open a ticket immediately; record **who reported, when, what they saw** (screenshots).
- [ ] Assign an incident lead and a scribe (keeps the timeline).

### 2. Contain (stop it spreading - don't destroy evidence)
- [ ] **Isolate** affected machines: unplug network / disable Wi-Fi / EDR network isolation. *Don't power off* unless told to.
- [ ] **Disable** compromised accounts; **revoke sessions** and reset passwords + MFA.
- [ ] Block malicious senders, domains, IPs, file hashes.
- [ ] If ransomware: protect backups (disconnect backup storage, check immutable copies).

### 3. Analyze
- [ ] What happened, how did they get in, what systems/data are affected, since when?
- [ ] Preserve evidence: logs (sign-ins, firewall, EDR), disk/memory images, emails. Note **chain of custody**.
- [ ] Is personal data involved? → inform the DPO now (GDPR: regulator within **72 hours** of awareness).

### 4. Eradicate & remediate
- [ ] Remove malware / reimage machines from known-good images.
- [ ] Close the entry point (patch, disable the abused feature, fix the misconfiguration).
- [ ] Reset credentials that may be exposed (including service accounts and keys).

### 5. Recover
- [ ] Restore from **verified clean** backups; bring systems back in priority order.
- [ ] Monitor closely for re-infection (at least 2 weeks).
- [ ] Confirm with users / business that service is back to normal.

### 6. Lessons learned (within 2 weeks)
- [ ] Blameless post-incident review (template: [postmortem](../../../system-administration-it-infrastructure-services/it-asset-runbook/templates/postmortem-template.md)).
- [ ] Update this runbook, the risk register, and controls.

## Never

- Pay a ransom without management, legal, and insurer involvement.
- Discuss the incident over a possibly compromised channel (use phone / out-of-band chat).
- Wipe a machine before evidence is captured.
