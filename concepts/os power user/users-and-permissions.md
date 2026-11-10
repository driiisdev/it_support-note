# Users, Groups & Permissions

Who is allowed to do what on a computer. Getting this right is half of IT security; getting it
wrong is a constant source of tickets ("Access denied") or breaches (everyone is admin).

## Users and groups

- **User account** - an identity: a username, credentials, a home folder, settings.
- **Group** - a collection of users. You grant permissions to **groups**, then add users to
  groups. (Never grant permissions to 50 individual users - when someone changes teams you'll
  never find them all.)
- **Principle of least privilege** - give people exactly the access they need, nothing more.

### Account types

| | Windows | Linux |
|---|---|---|
| Superuser | **Administrator** / members of the *Administrators* group | **root** (UID 0) |
| Normal user | Standard user | regular user |
| Temporary elevation | **UAC** prompt ("Run as administrator") | **`sudo`** (runs one command as root, logs it) |
| Service accounts | `SYSTEM`, `LocalService`, `NetworkService` | `www-data`, `nobody`, ... |

Daily work should happen as a **standard user**; elevate only when needed. That way malware the
user accidentally runs can't change the whole system.

### Local vs domain accounts (Windows)

- **Local account** - exists only on that one computer.
- **Domain account** - lives in **Active Directory**, works on every domain-joined computer.
  Companies use domain accounts. (See [Directory services](<../system administration it infrastructure services/directory-services.md>).)

## Managing users

### Windows

```powershell
# GUI: Computer Management (compmgmt.msc) -> Local Users and Groups
Get-LocalUser
Get-LocalGroupMember Administrators

$pw = Read-Host -AsSecureString "Password"
New-LocalUser -Name "jdoe" -Password $pw -FullName "Jane Doe"
Add-LocalGroupMember -Group "Users" -Member "jdoe"
Set-LocalUser -Name "jdoe" -Password $pw    # reset password
Disable-LocalUser -Name "jdoe"
Remove-LocalUser -Name "jdoe"

net user jdoe /logonpasswordchg:yes         # cmd: force change at next logon
```

### Linux

```bash
sudo useradd -m -s /bin/bash jdoe     # -m create home dir
sudo passwd jdoe                      # set password
sudo passwd -e jdoe                   # expire it -> must change at next login
sudo usermod -aG sudo jdoe            # add to group (-a = append! without it, other groups are removed)
groups jdoe
sudo usermod -L jdoe                  # lock account
sudo userdel -r jdoe                  # delete user + home
```

Where Linux keeps this:

| File | Contains |
|---|---|
| `/etc/passwd` | one line per user: `name:x:UID:GID:comment:home:shell` (no passwords anymore) |
| `/etc/shadow` | password **hashes** + expiry info, readable only by root |
| `/etc/group` | groups and their members |
| `/etc/sudoers` | who may use sudo (edit **only** with `visudo`) |

## Passwords

- Users should set their own; admins set a temporary one with **"must change at next logon."**
- Store and compare **hashes**, never plaintext.
- Enforce policies (length, lockout after failed attempts) centrally - see
  [The 3 As of cybersecurity](<../it security/the-3-as-of-cybersecurity.md>).

## Windows permissions (NTFS)

Every file/folder has an **ACL** (Access Control List) made of **ACEs** (entries: who + what).

| Permission | Allows |
|---|---|
| **Read** | open, view contents and attributes |
| **Read & execute** | read + run programs/scripts |
| **List folder contents** | see what's in a folder |
| **Write** | create files, change contents |
| **Modify** | read, write, **and delete** |
| **Full control** | everything, including changing permissions and taking ownership |

- **Inheritance** - folders pass permissions down to everything inside. Most "weird permission"
  issues are a broken inheritance somewhere.
- **Deny beats allow** - an explicit Deny ACE overrides an Allow.
- **Share permissions vs NTFS permissions** - on network shares, both apply and the **most
  restrictive** wins.

```powershell
icacls "D:\Finance"                                  # view
icacls "D:\Finance" /grant "Accountants:(OI)(CI)M"   # grant Modify, inherited by files (OI) & subfolders (CI)
icacls "D:\Finance" /remove "Everyone"
icacls "D:\Finance" /inheritance:d                   # disable inheritance (copy existing)
Get-Acl "D:\Finance" | Format-List
```

## Linux permissions

Every file has an **owner**, a **group**, and permissions for three classes:

```
-rwxr-x---  1  amina  devs  4096  Mar  4 10:12  deploy.sh
│└┬┘└┬┘└┬┘     │      │
│ │  │  │      owner  group
│ │  │  └── others: ---  (nothing)
│ │  └───── group:  r-x  (read, execute)
│ └──────── owner:  rwx  (read, write, execute)
└────────── type: - file, d directory, l symlink
```

| Letter | On a file | On a directory |
|---|---|---|
| r | read contents | list names inside |
| w | change contents | create/delete files inside |
| x | run as a program | enter it (`cd`) |

> 🖼️ **Image idea: `ls -l` permission string breakdown** - the string above with colored
> brackets for type / owner / group / others and the octal value under each triad.
> Suggested file: `assets/img/linux-permissions.png`
<!-- ![linux permissions](<../../assets/img/linux-permissions.png>) -->

### Changing permissions

**Symbolic mode:**

```bash
chmod u+x deploy.sh        # owner gets execute
chmod g-w report.txt       # group loses write
chmod o= secret.txt        # others get nothing
chmod a+r public.txt       # all get read
```

**Numeric (octal) mode** - r=4, w=2, x=1, add them per class:

| Octal | Meaning | Common use |
|---|---|---|
| `755` | rwxr-xr-x | scripts, directories |
| `644` | rw-r--r-- | normal files |
| `600` | rw------- | private keys (`~/.ssh/id_ed25519`) |
| `700` | rwx------ | private directories (`~/.ssh`) |
| `777` | everyone everything | almost never correct - a red flag |

```bash
chown amina:devs deploy.sh     # change owner and group
chgrp devs report.txt          # change group only
```

### Special permissions

| Bit | Effect | Example |
|---|---|---|
| **setuid** (`s` in owner x, octal 4000) | program runs as the **file's owner**, not the user who started it | `/usr/bin/passwd` (needs root to edit `/etc/shadow`) |
| **setgid** (`s` in group x, 2000) | runs with the file's group; on a directory, new files inherit the directory's group | shared team folders |
| **sticky** (`t`, 1000) | in a shared directory, users can only delete **their own** files | `/tmp` (`drwxrwxrwt`) |

## How it's used in real IT support

- "Access denied to the shared drive" → check group membership first, then the ACL, then share
  vs NTFS permissions. Group membership changes require the user to **log off and on**.
- New hire → create account, add to the right groups (not individual permissions).
- Leaver → **disable** the account first (don't delete immediately - you may need the data/mail).
- SSH key "permissions are too open" error → `chmod 600 ~/.ssh/id_*`.

## Practice project

[`practice/os-power-user/user-permissions-lab`](<../../practice/os-power-user/user-permissions-lab>) -
an onboarding/offboarding script driven by a CSV of new hires (PowerShell for Windows, Bash for
Linux, both with a safe **dry-run** default), plus a Python permission auditor that flags
world-writable files and explains `chmod` octal values.

## Related

- [Navigating the system](<navigating-the-system.md>) - the shell commands used here.
- [Directory services](<../system administration it infrastructure services/directory-services.md>) - users and groups at company scale.
- [The 3 As of cybersecurity](<../it security/the-3-as-of-cybersecurity.md>) - authorization in depth.
