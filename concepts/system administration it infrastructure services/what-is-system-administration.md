# What Is System Administration?

**System administration** is managing an organization's IT so that it is reliable, secure, and
fits what the business needs - servers, user devices, accounts, networks, and the policies around
them. In small companies, the IT support person *is* the sysadmin; in larger ones it's a separate
role that IT support escalates to.

## What sysadmins are responsible for

| Area | Examples |
|---|---|
| Users & hardware | onboarding/offboarding, laptops, phones, peripherals |
| Servers | file, print, email, web, database, directory servers |
| Infrastructure services | DNS, DHCP, NTP, VPN, backups |
| Policies | password policy, acceptable use, what users may install |
| Routine maintenance | patching, updates, monitoring, capacity planning |
| Troubleshooting | escalated tickets, outages |
| Vendors | ISPs, hardware suppliers, software licensing, support contracts |
| Security | access control, auditing, incident response |

## Servers

A **server** is any computer that provides a service to other computers (**clients**). It's a role,
not a type of hardware - but dedicated server hardware is built for reliability (redundant power
supplies, ECC RAM, hot-swappable disks, remote management such as iDRAC/iLO).

| Form factor | Description |
|---|---|
| **Tower** | looks like a desktop PC; small offices |
| **Rack** | flat, mounted in standard 19-inch racks; size measured in **U** (1U = 1.75 in) |
| **Blade** | very thin servers sharing power/cooling in a chassis; high density |

**KVM switch** - one keyboard/video/mouse controlling many servers in a rack.

### On-premises vs cloud

| | On-premises | Cloud |
|---|---|---|
| Cost | big upfront purchase (CapEx) | pay per use (OpEx) |
| Control | full control of hardware and data location | provider manages hardware |
| Scaling | buy and rack more servers (weeks) | add capacity in minutes |
| Responsibility | power, cooling, physical security, hardware failures are yours | provider's - but configuration and data are still yours |

Most organizations end up **hybrid**.

## Organizational policies

Policies answer "what are people allowed to do?" so that decisions are consistent and defensible:

- Can users install software? Who approves exceptions?
- Password requirements and MFA.
- Acceptable use of company devices and internet.
- Who gets admin rights (ideally: almost nobody, and only via separate admin accounts).

Policies should be **written down**, **communicated**, and **enforced technically** where possible
(Group Policy, MDM) rather than relying on people remembering.

## The hardware lifecycle

```
Procurement -> Deployment -> Maintenance -> Retirement
```

1. **Procurement** - standard models make support easier (same drivers, same spare parts).
2. **Deployment** - image, configure, assign to a user, record in the **asset inventory**
   (asset tag, serial number, model, user, location, purchase/warranty dates).
3. **Maintenance** - updates, repairs, warranty claims.
4. **Retirement** - wipe data securely (see [Company culture for security](<../it security/company-culture-for-security.md>)),
   update inventory, recycle or resell.

> 🖼️ **Image idea: hardware lifecycle** - circular diagram of the four stages with the key task of
> each stage.
> Suggested file: `assets/img/hardware-lifecycle.png`
<!-- ![hardware lifecycle](<../../assets/img/hardware-lifecycle.png>) -->

## Routine maintenance

- **Patch management** - apply updates on a schedule. Roll out in **batches**: test machines →
  a pilot group → everyone. Critical security fixes may skip the queue.
- **Monitoring** - disk space, CPU/memory, service uptime, backup success, certificate expiry.
  Alerts should go to a person *before* users notice.
- **Maintenance windows** - agreed times when changes/reboots are allowed (e.g. Sunday 02:00).

## Vendors

Sysadmins manage relationships with vendors: support contracts, warranty, SLAs (how fast they
must respond), renewals. Keep contacts, contract numbers, and expiry dates documented - you don't
want to look for them during an outage.

## Best practices

### Never test in production

**Production** = the live system people depend on. Test changes in a **test environment** first
(a VM, a staging server, a pilot group).

### Assess risk

For every change ask: what could go wrong? who's affected? how do we **roll back**?
Have a **backout plan** before you start.

### Fix things the right way

- **Reproduce** the problem first, so you can prove the fix works.
- Find the **root cause** instead of patching symptoms.
- Prefer **automation** for repeated tasks - scripts are consistent, humans aren't.

### Change management

A process for making changes in a controlled way:

```
Request -> Review risk & impact -> Approve -> Schedule (window) -> Implement -> Verify -> Document
```

Even a lightweight version (a ticket describing what/why/when/rollback) prevents most
"someone changed something and now it's broken" incidents.

### Post-mortems

After an incident, write a **blameless** post-mortem:

- **Summary** - what happened, impact, duration.
- **Timeline** - when it started, was detected, was fixed.
- **Root cause** - why it happened.
- **What went well / poorly.**
- **Action items** - specific changes, each with an owner, so it doesn't happen again.

Blameless means focusing on **processes and systems**, not punishing individuals - otherwise
people hide mistakes, and you stop learning from them.

### Documentation

Write down: how systems are configured, how to do recurring tasks (**runbooks**), network
diagrams, passwords (in a password manager, never in a spreadsheet), vendor contacts. Good
documentation is what lets you take a vacation.

## Practice project

[`practice/system-administration-it-infrastructure-services/it-asset-runbook`](<../../practice/system-administration-it-infrastructure-services/it-asset-runbook>) -
an asset inventory tool (CSV-backed: add assets, assign to users, flag expiring warranties,
report by status) plus ready-to-use templates for a runbook, a change request, and a blameless
post-mortem.

## Related

- [Troubleshooting](<../technical support fundamentals/troubleshooting.md>) - root cause and documentation.
- [Network and infrastructure services](<network-and-infrastructure-services.md>) - the services sysadmins run.
- [Data recovery & backups](<data-recovery-backups.md>) - planning for when things go wrong.
