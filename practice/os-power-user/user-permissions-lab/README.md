# Practice: User & Permissions Lab (Users and Permissions)

Concept note:
[`users-and-permissions.md`](<../../../concepts/os power user/users-and-permissions.md>)

## What this demonstrates

The everyday user lifecycle, done the way it should be done:

- **Onboarding from a CSV** - consistent usernames, a random temporary password with **"must
  change at next logon,"** and access granted through a **department group**, never to individuals.
- **Offboarding** - **disable** first (keep data for handover), remove group membership; don't
  delete on day one.
- **Shared folder permissions** - NTFS: the group gets *Modify* inherited `(OI)(CI)`; Linux: `2770`
  with **setgid** so new files belong to the department group.
- **Auditing** - spotting "Everyone: Modify," world-writable files, setuid binaries, and private
  keys readable by others.

Both scripts are **dry-run by default** - they print exactly what they would do.

## Scenario

HR sends the Monday list: four new hires and one contractor leaving. Each department has a shared
folder only that department may use. Last month someone "fixed" an access ticket by giving
Everyone access to the Finance folder - you need to find things like that, too.

## Folder structure

```
user-permissions-lab/
  new-hires.csv        <- first,last,department,action (onboard/offboard)
  Onboard-Users.ps1    <- Windows local users/groups + NTFS folders (dry run | -Apply | -Cleanup -Apply)
  onboard_users.sh     <- Linux users/groups + setgid shared folders (dry run | --apply | --cleanup --apply)
  perm_tool.py         <- explain chmod values; audit a folder (icacls on Windows, mode bits on Linux); demo
```

## Code walkthrough

**Permissions on groups, users in groups** (both scripts):

```powershell
icacls $folder /inheritance:r /grant:r "Administrators:(OI)(CI)F" "SYSTEM:(OI)(CI)F" "${group}:(OI)(CI)M"
#                ^ remove inherited ACEs  (OI)=files inherit (CI)=subfolders inherit  M=Modify
```

```bash
chown root:lab-finance /srv/labshares/Finance
chmod 2770 /srv/labshares/Finance   # setgid + rwx owner + rwx group + nothing for others
```

**Safe defaults that mirror real practice:**

- Temp password from a character set without look-alikes (`0/O`, `1/l`) and forced change at first
  logon (`net user <u> /logonpasswordchg:yes`, `passwd -e`).
- `usermod -aG` - the comment in the script explains why forgetting `-a` silently removes a user
  from every other group (a classic outage).
- Offboarding uses `Disable-LocalUser` / `usermod -L` + `nologin` shell.

**`perm_tool.py audit`** checks NTFS ACLs on Windows by parsing `icacls` for broad principals
(`Everyone`, `Users`, `Authenticated Users`) with write-level rights `(F)(M)(W)`, and POSIX mode
bits on Linux. `demo` creates a throwaway folder with the classic mistakes and audits it.

## Run it

```powershell
# Windows - dry run (safe anywhere)
powershell -ExecutionPolicy Bypass -File .\Onboard-Users.ps1
# for real - elevated PowerShell, ideally in a VM snapshot:
.\Onboard-Users.ps1 -Apply
Get-LocalGroupMember lab-Finance ; icacls C:\LabShares\Finance
.\Onboard-Users.ps1 -Cleanup -Apply
```

```bash
# Linux - dry run, then for real in a VM
./onboard_users.sh
sudo ./onboard_users.sh --apply
id abello ; ls -ld /srv/labshares/*
sudo ./onboard_users.sh --cleanup --apply
```

```bash
python perm_tool.py explain 755
python perm_tool.py explain rwxr-x---
python perm_tool.py explain 2770
python perm_tool.py demo
python perm_tool.py audit C:\Users\Public       # or any folder you own
```

Expected (`perm_tool.py demo` on Windows):

```
[HIGH] ...\finance: Everyone:(OI)(CI)(M) -> broad group can write/modify
[HIGH] ...\finance\salaries.xlsx: Everyone:(I)(M) (inherited) -> broad group can write/modify
```

> Tested note: the dry runs and `perm_tool.py` were run on Windows. The `-Apply` / `--apply`
> paths create real accounts, so they weren't run on a personal machine - do that part in a VM
> with a snapshot.

## Try this yourself

- After `-Apply`, log in as `abello` (temp password), confirm Windows forces a password change, then
  try opening `C:\LabShares\HR` → Access denied. That's least privilege working.
- Add `abello` to `lab-HR` while she's logged in - access still fails until she **logs off and on**
  (group membership lives in the logon token). This explains a lot of "I added them and it still
  doesn't work" tickets.
- Add an explicit **Deny** for one user on the Finance folder and watch it beat the group's Allow.
- On Linux, create a file in `/srv/labshares/Finance` as `abello` and check `ls -l` - the group is
  `lab-finance` thanks to setgid, not her personal group.
- Extend the CSV with a `manager` column and make the PowerShell script write a welcome summary
  per user (username, groups, folder) to a text file for the manager.

## Real-world equivalent

- In companies this is done in **Active Directory / Entra ID** (`New-ADUser`, AD groups), usually
  triggered by HR systems - see the [ad-bulk-provisioning](../../system-administration-it-infrastructure-services/ad-bulk-provisioning)
  project. The principles are identical: groups, least privilege, disable-before-delete.
- Permission audits are a standard part of security reviews and compliance (who can access
  financial/HR data, and why?).
