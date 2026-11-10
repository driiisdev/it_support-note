# Troubleshooting & Customer Service

Troubleshooting is the core skill of IT support: **finding the cause of a problem, fixing it, and
making sure it doesn't come back**. Customer service is how you do that without making the
user's day worse. Both are learnable methods, not talents.

## The troubleshooting method

```
1. Ask questions        -> understand the actual problem
2. Isolate the problem  -> shrink where the cause could be
3. Follow the crumbs    -> logs, error messages, timeline: "what changed?"
4. Start simple         -> quickest/cheapest fixes first
5. Fix the root cause   -> not just the symptom
6. Verify + document    -> confirm with the user, write it up
```

> 🖼️ **Image idea: troubleshooting flowchart** - the six steps above as a loop, with "not fixed?"
> arrows going back to step 2.
> Suggested file: `assets/img/troubleshooting-flow.png`
<!-- ![troubleshooting flow](<../../assets/img/troubleshooting-flow.png>) -->

### 1. Ask questions

Users describe *symptoms*, not causes. Good questions turn "it's broken" into something testable:

- **What exactly happens?** Any error message? (Ask for a screenshot.)
- **When did it start?** What changed around then (update, new software, moved desks)?
- **Can you reproduce it?** Every time, or randomly?
- **Who's affected?** Just you, your team, everyone? (One user = their device/account;
  everyone = a server/network/service.)
- **What have you already tried?**

Avoid yes/no questions at the start - open questions get more information.

### 2. Isolate the problem

Cut the problem space in half, again and again (binary search):

- Works on another computer? → problem is the original computer, not the account/service.
- Works for another user on the same computer? → problem is the user's profile/permissions.
- Works in another browser? → problem is the browser (cache, extension), not the website.
- Works on a wired connection but not Wi-Fi? → problem is wireless.

Change **one thing at a time** - if you change three things and it works, you don't know which
one fixed it.

### 3. Follow the cookie crumbs

- **Error messages** - search the exact text (or error code).
- **Logs** - Windows Event Viewer, `/var/log/` on Linux, application logs.
- **Timeline** - "it worked Friday, not Monday" → what happened over the weekend? (updates
  installed, password expired, certificate expired...)

### 4. Start with the quickest step first

Order by *likelihood × cheapness*:

1. Restart the app / reboot the device (clears a surprising number of issues - memory leaks,
   stuck processes, pending updates).
2. Check the obvious: cable plugged in? Caps Lock on? Correct account? Device on?
3. Check known issues (is there an outage? is a service down for everyone?).
4. Then the slower stuff: reinstalling, reimaging, replacing hardware.

### 5. Fix the root cause

"Reboot fixed it" is fine for today, but if it happens weekly there's an underlying cause
(e.g. a memory leak in one app). The **root cause** is the thing that, if fixed, stops the
problem from recurring. Asking "why?" repeatedly (the *5 whys*) helps:

```
Laptop is slow.               Why? -> disk is 100% busy.
Disk is 100% busy.            Why? -> antivirus is scanning constantly.
Antivirus scans constantly.   Why? -> it's scanning a huge sync folder on every change.
Root cause: AV exclusion missing for the sync folder.  Fix: add exclusion (per policy).
```

### 6. Verify and document

- Confirm with the user that it's actually fixed **for them**, in **their** workflow.
- Write it down in the ticket: symptoms, cause, fix. If it'll happen again, write a
  **knowledge-base (KB) article**.

## Getting through a hard problem

- **Take a break** - fresh eyes find obvious things.
- **Escalate** when it's beyond your access, skills, or time budget. Escalating isn't failing;
  it's routing the problem to the right person. Include everything you've already tried so they
  don't repeat it.
- **Learn from it** - post-mortems for big incidents: what happened, why, what we'll change.

## Customer service

### Empathy

The user is often stressed (deadline, lost work). Acknowledge it: *"That's frustrating, especially
before a presentation - let's get it sorted."* You're on the same side: you vs. the problem,
not you vs. the user.

### Communication

- Use **plain language**. Not "your DHCP lease expired," but "your computer didn't get an
  address from the network, so I renewed it."
- **Set expectations**: what you'll do, how long it'll take, when you'll update them.
- **Don't blame** the user, even if they caused it. Explain how to avoid it next time.
- **Intros and outros matter**: introduce yourself; at the end, confirm it's fixed and ask if
  there's anything else.

### Handling difficult situations

- Stay calm and professional; don't take frustration personally.
- Listen fully before responding; repeat back what you heard.
- If you made a mistake, own it and fix it.
- If someone is abusive, follow your organization's policy and escalate to a manager.

### Remote vs in-person vs ticket

| Channel | Tips |
|---|---|
| In person | be on time, respect their workspace, explain what you're doing |
| Phone | confirm identity, narrate steps clearly, avoid long silences |
| Remote session | ask permission before taking control; say when you're done |
| Email / chat / ticket | clear subject, numbered steps, screenshots, friendly but concise |

## Documentation and tickets

A good ticket is a mini case study someone else can pick up:

```
Title:     Outlook won't send - "Cannot connect to server" (user: j.doe)
Reported:  2026-03-04 09:12 by phone
Impact:    1 user, can receive but not send
Symptoms:  Error 0x800CCC0E on send since this morning
Tried:     restart Outlook (no), webmail works (yes) -> account fine, client issue
Cause:     Outlook profile still pointing at old SMTP server after migration
Fix:       Recreated mail profile; test email sent successfully
Follow-up: KB article "Outlook send fails after mail migration" - check other migrated users
```

## Practice project

[`practice/technical-support-fundamentals/helpdesk-troubleshooting`](<../../practice/technical-support-fundamentals/helpdesk-troubleshooting>) -
a small CLI ticket tracker (create, update, close tickets with the fields above, saved to JSON)
plus a connectivity checker that applies the "isolate the problem" method to a network outage.

## Related

- [Introduction](<introduction.md>) - the layers of a computer, used to isolate problems.
- [Networking](<networking.md>) - "work outward" network troubleshooting.
- [What is system administration](<../system administration it infrastructure services/what-is-system-administration.md>) - change management and post-mortems.
