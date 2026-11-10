# Understanding Security Threats

Before you can defend anything you need the vocabulary: what attackers want, what kinds of
malware exist, and how network, client-side, password, and deception attacks work.

## The CIA triad

Every security control protects one or more of these:

| Principle | Means | Attack example | Defense example |
|---|---|---|---|
| **Confidentiality** | only authorized people can see the data | data leak, eavesdropping | encryption, access control |
| **Integrity** | data isn't changed without authorization | tampering, MITM edits | hashes, digital signatures |
| **Availability** | data/systems are accessible when needed | DoS, ransomware | redundancy, backups |

> 🖼️ **Image idea: CIA triad triangle** - a triangle with one principle per corner and example
> controls next to each.
> Suggested file: `assets/img/cia-triad.png`
<!-- ![cia triad](<../../assets/img/cia-triad.png>) -->

## Essential terms

| Term | Definition |
|---|---|
| **Risk** | the chance something bad happens (likelihood × impact) |
| **Vulnerability** | a weakness that could be exploited (unpatched software, weak password) |
| **Zero-day** | a vulnerability unknown to the vendor - no patch exists yet |
| **Exploit** | code or technique that takes advantage of a vulnerability |
| **Threat** | something with the potential to cause harm (a person, malware, a flood) |
| **Hacker** | black hat (malicious), white hat (ethical, with permission), grey hat (in between) |
| **Attack** | an actual attempt to cause harm |
| **Attack surface** | all the points where an attacker could try to get in |

## Malware

**Mal**icious soft**ware** - software designed to harm, steal, or take control.

| Type | How it works |
|---|---|
| **Virus** | attaches to a legitimate file/program; spreads when that file is run or shared |
| **Worm** | spreads **by itself** across networks, no user action needed |
| **Trojan** | disguised as something useful; the user installs it themselves |
| **Spyware** | secretly monitors the user (browsing, data) |
| **Keylogger** | records keystrokes - passwords, messages |
| **Adware** | floods the user with ads; often bundled with free software |
| **Ransomware** | encrypts files and demands payment for the key |
| **Rootkit** | hides deep in the system (sometimes the kernel) with admin control; hides itself and other malware |
| **Backdoor** | a secret way into a system that bypasses normal authentication |
| **Botnet** | many infected machines ("bots") controlled together - used for DDoS, spam, crypto mining |
| **Logic bomb** | malicious code that triggers on a condition (a date, a user being deleted) |

Signs of infection: sudden slowness, pop-ups, browser homepage changed, unknown programs, files
encrypted/renamed, antivirus disabled, unusual network traffic.

**Ransomware response basics**: disconnect the machine from the network immediately, don't power
it off without guidance (memory evidence), escalate to security, restore from (clean, offline)
backups.

## Network attacks

| Attack | How it works |
|---|---|
| **DNS cache poisoning** | tricking a DNS server into caching a fake record → users sent to an attacker's site |
| **Man-in-the-middle (MITM)** | attacker places themselves between two parties to read/modify traffic (e.g. session hijacking, ARP spoofing) |
| **Rogue access point** | an unauthorized AP plugged into the company network - a backdoor around the firewall |
| **Evil twin** | a fake Wi-Fi network with the same name as a real one, to capture traffic/credentials |
| **DoS** | overwhelm a service so legitimate users can't use it |
| **DDoS** | DoS from many sources at once (often a botnet) - much harder to block |

DoS examples:

- **Ping of death** - malformed oversized ICMP packet crashing old systems.
- **Ping flood** - massive ICMP echo requests.
- **SYN flood** - sending many TCP SYNs and never completing the handshake, filling the server's
  half-open connection table.

> 🖼️ **Image idea: man-in-the-middle** - user ↔ attacker ↔ server, with the attacker reading and
> relaying both sides.
> Suggested file: `assets/img/mitm.png`
<!-- ![mitm](<../../assets/img/mitm.png>) -->

## Client-side attacks (injection)

| Attack | How it works |
|---|---|
| **Cross-site scripting (XSS)** | injecting malicious JavaScript into a website that runs in other users' browsers (e.g. to steal session cookies) |
| **SQL injection** | entering SQL code into an input field so the app runs it against its database: `' OR '1'='1` |

Defenses are on the application side: validating input, parameterized queries, output encoding.

## Password attacks

| Attack | How it works | Defense |
|---|---|---|
| **Brute force** | try every possible combination | long passwords, lockout policies, MFA |
| **Dictionary** | try common words and leaked passwords | ban common passwords, length > complexity |
| **Credential stuffing** | reuse username/password pairs leaked from other sites | unique passwords (password manager), MFA |

**CAPTCHAs** and **account lockouts** slow down automated online guessing.

## Deceptive attacks (social engineering)

Attacking the **human**, not the computer - usually the easiest way in.

| Attack | Description |
|---|---|
| **Phishing** | fake emails/messages that trick users into clicking a link, opening a file, or entering credentials |
| **Spear phishing** | phishing targeted at a specific person using personal details |
| **Whaling** | spear phishing aimed at executives |
| **Vishing / smishing** | phishing by voice call / SMS |
| **Spoofing** | faking the sender (email "From", caller ID, website look-alike) |
| **Baiting** | leaving infected USB drives where people will find them |
| **Tailgating** | following an authorized person through a secure door |
| **Shoulder surfing** | watching someone type their password |
| **Dumpster diving** | searching trash for documents, notes, old hardware |
| **Pretexting** | a made-up scenario ("I'm from IT, I need your password to fix your account") |

### Recognizing a phishing email

- **Urgency or fear**: "Your account will be closed in 24 hours."
- **Sender mismatch**: display name says "Microsoft" but the address is `support@micros0ft-help.co`.
- **Link mismatch**: link text says one domain, actual URL (hover!) goes elsewhere.
- **Unexpected attachments**: `.zip`, `.html`, `.iso`, or Office files asking to "enable macros".
- **Requests for credentials, payment, gift cards, or MFA codes.**
- **Failed authentication** in headers (SPF/DKIM/DMARC fail).

IT will **never** ask for your password. Report suspicious emails (the "Report phishing" button)
rather than just deleting them, so others can be protected.

## Practice project

[`practice/it-security/phishing-analyzer`](<../../practice/it-security/phishing-analyzer>) -
parses `.eml` files (samples included, all fictional), checks SPF/DKIM/DMARC results in the
headers, finds `From` vs `Reply-To` mismatches, link-text vs real-URL mismatches, look-alike
domains, risky attachments, and urgency language - and produces a risk score with explanations.

## Related

- [Pelcgbybtl (cryptology)](<pelcgbybtl-cryptology.md>) - the tools that protect confidentiality and integrity.
- [Securing your networks](<securing-your-networks.md>) - defending against network attacks.
- [Company culture for security](<company-culture-for-security.md>) - training users against social engineering.
