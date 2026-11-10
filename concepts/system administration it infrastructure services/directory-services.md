# Directory Services: LDAP, Active Directory & Group Policy

When a company has 500 people and 600 computers, you can't create accounts on each machine. A
**directory service** stores users, groups, computers, and policies **centrally**, so one account
works everywhere and one change applies everywhere.

## What is a directory server?

A database optimized for **lots of reads, few writes**, organized as a **hierarchical tree** of
objects (users, groups, computers, printers) with attributes (name, email, department, phone).

Benefits:

- **Centralized authentication** - one username/password for every company computer and app.
- **Centralized management** - disable one account and the person loses access everywhere.
- **Replication** - multiple directory servers copy the data to each other for redundancy and
  speed at remote sites.

Standards and products:

- **X.500** - the original directory standard (1980s).
- **LDAP** - the lightweight protocol used to **access** directories.
- **Active Directory (AD)** - Microsoft's directory service (by far the most common in companies).
- **OpenLDAP** - open-source directory server.
- Cloud: **Microsoft Entra ID** (formerly Azure AD), Google Cloud Identity, Okta (identity).

## LDAP - Lightweight Directory Access Protocol

Port **389** (LDAP, optionally upgraded with StartTLS) and **636** (LDAPS - LDAP over TLS).

### Operations

| Operation | Does |
|---|---|
| **Bind** | authenticate to the directory |
| **Search** | find entries matching a filter |
| **Add / Delete** | create / remove an entry |
| **Modify** | change attributes |
| **Compare** | check if an attribute has a value |

**Bind types**: anonymous, **simple** (username + password - only safe over TLS), **SASL** (e.g.
Kerberos).

### Distinguished names

Every object has a unique **DN** describing its place in the tree, read right to left:

```
CN=Jane Doe,OU=Sales,OU=Users,DC=corp,DC=example,DC=com
│           │        │        └──────── domain: corp.example.com
│           │        └── OU "Users"
│           └── inside OU "Sales"
└── Common Name: the object itself
```

| Abbreviation | Meaning |
|---|---|
| **DC** | Domain Component |
| **OU** | Organizational Unit (a folder/container) |
| **CN** | Common Name |

> 🖼️ **Image idea: directory tree** - `corp.example.com` at the top, OUs for Users / Computers /
> Groups, sub-OUs for departments, with the DN of one user traced along the path.
> Suggested file: `assets/img/directory-tree.png`
<!-- ![directory tree](<../../assets/img/directory-tree.png>) -->

### OpenLDAP tools and LDIF

Changes are often written in **LDIF** (LDAP Data Interchange Format):

```ldif
dn: uid=jdoe,ou=People,dc=example,dc=com
objectClass: inetOrgPerson
cn: Jane Doe
sn: Doe
uid: jdoe
mail: jdoe@example.com
```

```bash
ldapadd    -x -D "cn=admin,dc=example,dc=com" -W -f jdoe.ldif
ldapsearch -x -b "dc=example,dc=com" "(uid=jdoe)"
ldapmodify -x -D "cn=admin,dc=example,dc=com" -W -f change.ldif
ldappasswd -x -D "cn=admin,dc=example,dc=com" -W -S "uid=jdoe,ou=People,dc=example,dc=com"
```

## Active Directory

### Core concepts

| Term | Meaning |
|---|---|
| **Domain** | a security/administrative boundary, named like a DNS domain (`corp.example.com`) |
| **Domain controller (DC)** | a server that stores the AD database and authenticates users. Always have at least **two**. |
| **Tree** | domains sharing a contiguous namespace (`corp.example.com`, `eu.corp.example.com`) |
| **Forest** | the top-level container: one or more trees that trust each other |
| **OU** | a container for organizing objects and **applying Group Policy** |
| **Object** | a user, group, computer, printer... |

AD **depends on DNS** (clients find DCs via SRV records like `_ldap._tcp.dc._msdcs.corp.example.com`)
and on **time sync** (Kerberos allows max 5 min skew by default).

**FSMO roles** - five special jobs held by specific DCs (e.g. the **PDC emulator** handles
password changes and is the domain's time source).

### Users and groups

**Group types**:

- **Security groups** - used to grant permissions (file shares, apps). Also usable as mailing lists.
- **Distribution groups** - email lists only; can't be used for permissions.

**Group scopes**:

| Scope | Can contain | Use |
|---|---|---|
| **Domain local** | users/groups from anywhere in the forest | assign permissions to a resource |
| **Global** | users/groups from the same domain | group people by role (e.g. "Sales") |
| **Universal** | users/groups from any domain in the forest | multi-domain forests |

Classic best practice (**AGDLP**): **A**ccounts go in **G**lobal groups, global groups go into
**D**omain **L**ocal groups, domain local groups get **P**ermissions.

### Common admin tasks

```powershell
# Requires the ActiveDirectory module (RSAT) and domain rights
Get-ADUser jdoe -Properties LastLogonDate, LockedOut, PasswordLastSet
New-ADUser -Name "Jane Doe" -SamAccountName jdoe -UserPrincipalName jdoe@corp.example.com `
  -Path "OU=Sales,OU=Users,DC=corp,DC=example,DC=com" `
  -AccountPassword (Read-Host -AsSecureString "Temp password") -ChangePasswordAtLogon $true -Enabled $true
Add-ADGroupMember -Identity "Sales" -Members jdoe
Unlock-ADAccount jdoe
Set-ADAccountPassword jdoe -Reset -NewPassword (Read-Host -AsSecureString "New password")
Set-ADUser jdoe -ChangePasswordAtLogon $true
Disable-ADAccount jdoe
Search-ADAccount -LockedOut
Search-ADAccount -AccountInactive -TimeSpan 90.00:00:00 -UsersOnly
```

GUI: **Active Directory Users and Computers** (`dsa.msc`), Active Directory Administrative Center.

### Password resets - verify first

The #1 AD ticket. Before resetting: **verify the caller's identity** per policy (callback to a
known number, manager approval, ID check) - "I'm the CEO, reset my password now" is a classic
social-engineering attack. Then set a temporary password with **change at next logon**.

### Joining a computer to the domain

```powershell
Add-Computer -DomainName corp.example.com -OUPath "OU=Laptops,OU=Computers,DC=corp,DC=example,DC=com" -Restart
```

Requires: correct DNS server (the DC), network access to the DC, and an account with join rights.

## Group Policy

**Group Policy Objects (GPOs)** apply settings to users and computers in an OU (or site/domain).

- **Computer Configuration** - applies at startup to the machine (e.g. firewall rules, BitLocker,
  software installs).
- **User Configuration** - applies at logon to the user (e.g. mapped drives, desktop wallpaper,
  restricted Control Panel).
- **Policies** - enforced; users can't change them; removed when the GPO no longer applies.
- **Preferences** - set an initial value that users may change (e.g. a mapped drive).

### Processing order: LSDOU

```
Local policy -> Site -> Domain -> OU (parent -> child)
```

Later wins on conflict, so the **closest OU wins** - unless a GPO is **Enforced** or an OU
**Blocks inheritance**.

```powershell
gpupdate /force          # apply policy now (instead of waiting ~90 min)
gpresult /r              # which GPOs applied to this user/computer
gpresult /h report.html  # detailed HTML report
```

**RSoP** (Resultant Set of Policy) = the final combined result of all GPOs that apply - what
`gpresult` shows.

> 🖼️ **Image idea: GPO inheritance (LSDOU)** - nested boxes (Site ⊃ Domain ⊃ OU ⊃ child OU) with
> GPOs attached at each level and the winning setting highlighted.
> Suggested file: `assets/img/gpo-lsdou.png`
<!-- ![gpo lsdou](<../../assets/img/gpo-lsdou.png>) -->

### Troubleshooting Group Policy

| Symptom | Check |
|---|---|
| Policy not applying | is the user/computer in the right OU? `gpresult /r`; security filtering; is it a computer setting applied to a user OU (or vice versa)? |
| Applies to some PCs only | replication between DCs; WMI filters; slow link detection |
| Can't log on: "trust relationship failed" | computer account password out of sync → rejoin domain (or `Reset-ComputerMachinePassword`) |
| Logon errors about time | clock skew → NTP |

## Practice project

[`practice/system-administration-it-infrastructure-services/ad-bulk-provisioning`](<../../practice/system-administration-it-infrastructure-services/ad-bulk-provisioning>) -
reads a CSV of new hires, validates it, generates usernames (handling duplicates), builds the
correct OU DN per department, and outputs **both** a PowerShell AD script and an LDIF file for
OpenLDAP - reviewable before anything touches a real directory. Includes a DN parser and an
LSDOU "which GPO wins" simulator.

## Related

- [Users and permissions](<../os power user/users-and-permissions.md>) - local users and groups.
- [Network and infrastructure services](<network-and-infrastructure-services.md>) - the DNS and NTP AD relies on.
- [The 3 As of cybersecurity](<../it security/the-3-as-of-cybersecurity.md>) - Kerberos and authentication.
