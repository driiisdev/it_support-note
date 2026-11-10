# Practice: AD Bulk Provisioning & GPO Simulator (Directory Services)

Concept note:
[`directory-services.md`](<../../../concepts/system administration it infrastructure services/directory-services.md>)

## What this demonstrates

- **`provision.py`** - the real-world version of "create these new users": an HR CSV becomes a
  **reviewable** PowerShell script for **Active Directory** (`New-ADUser`, `Add-ADGroupMember`, all
  in `-WhatIf` mode) **and** an **LDIF** file for **OpenLDAP**. It handles the parts that go wrong by
  hand: validation, accented names, apostrophes, 20-character sAMAccountName limit, duplicate
  usernames, OU placement, group membership.
- **`gpo_sim.py`** - "why didn't my GPO apply?": simulates **LSDOU** processing order,
  **Block Inheritance**, and **Enforced** links, and prints the resulting policy like `gpresult /r`.
  Includes a DN parser that handles escaped commas.

No real directory is touched - you can run everything on any machine.

## Scenario

HR emails a spreadsheet of new starters every Friday. Last time someone typed them in by hand: two
people got the same username, one landed in the wrong OU (so no drive mappings), and an accented
name broke a login script. You build a pipeline where a human reviews generated changes before
anything is applied.

## Folder structure

```
ad-bulk-provisioning/
  new-hires.csv        <- HR export (includes deliberate problems: accents, duplicates, long names, a blank name)
  existing-users.txt   <- usernames already in the directory (to avoid collisions)
  provision.py         <- validate + generate out/New-ADUsers.ps1 and out/new-users.ldif
  gpo_sim.py           <- LSDOU / Enforced / Block Inheritance simulator + DN parser
  out/                 <- generated files (gitignored)
```

## Code walkthrough

**Usernames that survive real names:**

```python
unicodedata.normalize("NFKD", "José Muñoz").encode("ascii", "ignore")  # -> "Jose Munoz"
re.sub(r"[^A-Za-z0-9]", "", "O'Neill")                                 # -> "ONeill"
# abello already exists -> abello2 -> abello3 ...
# max 20 chars for sAMAccountName (pre-Windows 2000 logon name)
```

**DNs are written bottom-up** - the OU mapping is top-down (`Users > Sales > EMEA`) but the DN reverses it:

```
CN=José Muñoz,OU=EMEA,OU=Sales,OU=Users,DC=corp,DC=example,DC=com
```

Special characters in a DN (`,` `+` `"` `\` `<` `>` `;` `=`) are backslash-escaped; the PowerShell
output escapes `'` as `''`. Both are classic sources of broken scripts.

**Safety by default**: the generated script sets `$WhatIf = $true` and passes `-WhatIf:$WhatIf` to
every command, so the first run only *shows* what would happen.

**GPO precedence** in `gpo_sim.py`:

```
Local -> Site -> Domain -> parent OU -> child OU      later wins
Block Inheritance on an OU  -> skip site/domain/parent-OU links (not the local policy)...
...unless the link is Enforced -> always applies, and beats links below it
```

In the sample, *Finance Apps* tries to allow USB storage, but the domain-level *Security Baseline* is
**Enforced**, so `USB storage = Blocked` still wins. The *Lab* OU blocks inheritance, so it loses the
drive mappings and proxy - but not the enforced baseline.

> Simplification: in real AD, the *password policy* for domain accounts comes from the domain level
> and is applied by the domain controllers, so blocking inheritance on an OU doesn't exempt users
> from it. The simulator treats it like any other setting.

## Run it

```bash
python provision.py
python provision.py --domain mylab.local
python gpo_sim.py
python gpo_sim.py "CN=Jane Doe,OU=Lab,OU=Users,DC=corp,DC=example,DC=com"
```

Expected:

```
USERNAME            NAME                                DISTINGUISHED NAME
abello2             Amina Bello                         CN=Amina Bello,OU=Finance,OU=Users,DC=corp,...
jmunoz              José Muñoz                          CN=José Muñoz,OU=EMEA,OU=Sales,OU=Users,...
abello3             Aminat Bello                        ...
cmontgomerywelling  Christopher-Alexander Montgomery-We ...
7 of 8 rows accepted.
  - line 9: first and last name are required

Resultant Set of Policy (what gpresult /r would show):
  USB storage            = Blocked              from Security Baseline (enforced)
  Screen lock (min)      = 5                    from Finance Apps
```

## Try this yourself

- **Build a real lab**: a Windows Server VM, promote it to a domain controller
  (`Install-WindowsFeature AD-Domain-Services` → `Install-ADDSForest -DomainName mylab.local`),
  create the OUs, run `provision.py --domain mylab.local`, review, set `$WhatIf = $false`, run it.
  Then join a Windows client VM and log in as one of the users.
- **OpenLDAP lab**: in an Ubuntu VM, `sudo apt install slapd ldap-utils`, then
  `ldapadd -x -D "cn=admin,dc=..." -W -f out/new-users.ldif` and `ldapsearch -x -b "dc=..." "(uid=jmunoz)"`.
- Add an **offboarding** mode: from a leavers CSV, generate `Disable-ADAccount`, move to an
  `OU=Disabled` OU, remove group memberships, and set the description to the leave date.
- Extend `gpo_sim.py` with **security filtering** (a GPO that only applies to members of a group)
  and **loopback processing**.
- On a domain-joined PC: `gpresult /r` and `gpresult /h report.html` - compare the real thing to the sim.

## Real-world equivalent

- HR-driven provisioning: Microsoft Entra ID / AD connected to HR systems (Workday, SuccessFactors),
  identity governance tools (SailPoint, Okta Lifecycle) - all do this validate → generate username →
  place → group pipeline.
- `gpresult`, **Group Policy Results** in GPMC, and RSoP (`rsop.msc`) are the real versions of
  `gpo_sim.py`.
