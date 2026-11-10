# Navigating the System: Windows & Linux Command Line

The GUI is fine for one machine. The **command line** is how you work fast, work remotely, and
automate. This note puts the Windows (PowerShell / cmd) and Linux (Bash) versions of each task
side by side.

## Shells

| OS | Shell | Notes |
|---|---|---|
| Windows | **PowerShell** | modern, object-based (commands pass objects, not text). Command names are `Verb-Noun`. Has aliases like `ls`, `cd`, `cat` for familiarity. |
| Windows | **Command Prompt** (`cmd.exe`) | legacy, still used in older scripts (`dir`, `copy`, `del`). |
| Linux / macOS | **Bash** / **zsh** | text-based, everything is a file; commands are small tools chained with pipes. |

## Paths

```
Windows:  C:\Users\amina\Documents\report.docx      (backslash, drive letters)
Linux:    /home/amina/Documents/report.docx          (forward slash, single root "/")
```

- **Absolute path** - starts from the root (`C:\` or `/`). Works from anywhere.
- **Relative path** - from where you are now: `Documents\report.docx`.
- `.` = current directory, `..` = parent directory, `~` = your home directory.
- Paths with spaces need quotes: `cd "C:\Program Files"`.
- Linux paths are **case-sensitive** (`Report.txt` ≠ `report.txt`); Windows paths are not.

> 🖼️ **Image idea: directory tree comparison** - Windows `C:\` tree (Users, Windows, Program Files)
> next to the Linux `/` tree (home, etc, var, usr, bin, tmp) with each folder's purpose.
> Suggested file: `assets/img/fs-hierarchy-windows-vs-linux.png`
<!-- ![filesystem hierarchy](<../../assets/img/fs-hierarchy-windows-vs-linux.png>) -->

### Important Linux directories

| Directory | Contains |
|---|---|
| `/home` | users' home folders |
| `/root` | the root user's home |
| `/etc` | system configuration files |
| `/var` | variable data - **logs** (`/var/log`), caches, spool |
| `/bin`, `/usr/bin` | programs/commands |
| `/tmp` | temporary files |
| `/dev` | device files (disks, terminals) |
| `/proc` | virtual files with live kernel/process info |

## Command cheat sheet

| Task | PowerShell | cmd | Bash |
|---|---|---|---|
| Where am I? | `Get-Location` (`pwd`) | `cd` | `pwd` |
| List files | `Get-ChildItem` (`ls`, `dir`) | `dir` | `ls -la` |
| Include hidden | `Get-ChildItem -Force` | `dir /a` | `ls -a` |
| Change directory | `Set-Location` (`cd`) | `cd` | `cd` |
| Make directory | `New-Item -ItemType Directory x` (`mkdir`) | `mkdir` | `mkdir -p a/b/c` |
| Copy | `Copy-Item a b` (`cp`) | `copy` / `xcopy` / `robocopy` | `cp`, `cp -r` (folders) |
| Move / rename | `Move-Item`, `Rename-Item` (`mv`) | `move`, `ren` | `mv` |
| Delete | `Remove-Item` (`rm`); `-Recurse` for folders | `del`, `rmdir /s` | `rm`, `rm -r` |
| Show file | `Get-Content` (`cat`) | `type` | `cat`, `less`, `head`, `tail` |
| Follow a log live | `Get-Content log.txt -Wait -Tail 20` | - | `tail -f log.txt` |
| Search inside files | `Select-String -Path *.log -Pattern error` | `findstr` | `grep -i error *.log` |
| Find files by name | `Get-ChildItem -Recurse -Filter *.pdf` | `dir /s *.pdf` | `find . -name "*.pdf"` |
| Help | `Get-Help Copy-Item -Examples` | `copy /?` | `man cp`, `cp --help` |
| History | `Get-History`, ↑ key | `doskey /history` | `history`, ↑, `Ctrl+R` |
| Clear screen | `Clear-Host` (`cls`) | `cls` | `clear` |

**Tab completion** works in all shells - type part of a name and press Tab. It saves time and
prevents typos.

> ⚠️ `rm -rf` (Linux) and `Remove-Item -Recurse -Force` (PowerShell) delete **without** the recycle
> bin. Double-check the path. Run `ls` on it first.

## Wildcards

| Pattern | Matches |
|---|---|
| `*` | any number of characters: `*.log` |
| `?` | exactly one character: `file?.txt` |
| `[abc]` (Bash) | one of a, b, c |

## Hidden files

- Windows: a file attribute (`attrib +h file`, or `Get-ChildItem -Force` to see them).
- Linux: any file whose name **starts with a dot** (`.bashrc`, `.ssh/`).

## Input, output, and redirection

Every program has three standard streams:

| Stream | Number | Default |
|---|---|---|
| stdin (input) | 0 | keyboard |
| stdout (output) | 1 | screen |
| stderr (errors) | 2 | screen |

| Operator | Meaning | Example |
|---|---|---|
| `>` | send stdout to a file (overwrite) | `ipconfig /all > net.txt` |
| `>>` | append | `echo "done" >> log.txt` |
| `2>` | send errors to a file | `cmd 2> errors.txt` |
| `2>&1` | merge errors into output | `cmd > all.txt 2>&1` |
| `<` | read stdin from a file | `sort < names.txt` |
| `\|` | pipe: output of one becomes input of the next | `cat log \| grep ERROR \| wc -l` |

### Pipes: text (Bash) vs objects (PowerShell)

```bash
# Bash passes text - you cut columns out of it
ps aux | sort -k4 -nr | head -5            # top 5 by memory %
```

```powershell
# PowerShell passes objects - you pick properties by name
Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 5 Name, Id, WorkingSet64
Get-ChildItem C:\Logs -Recurse | Where-Object Length -gt 100MB
```

## Text editors in the terminal

- Linux: `nano` (easy), `vim` (powerful, `:wq` to save and quit, `:q!` to quit without saving).
- Windows: `notepad file.txt` from the shell; or VS Code (`code file.txt`).

## How it's used in real IT support

- Remoting into a server over SSH where there's **no GUI** at all.
- Grabbing a user's network config into a file to attach to a ticket: `ipconfig /all > C:\temp\net.txt`.
- Finding which log file mentions an error: `Select-String` / `grep -r`.
- Cleaning up huge files filling a disk: `Get-ChildItem -Recurse | Sort-Object Length -Descending`.

## Practice project

[`practice/os-power-user/shell-navigation-lab`](<../../practice/os-power-user/shell-navigation-lab>) -
a setup script that builds a fake messy "user profile" folder (logs, duplicates, hidden files,
large files), then a list of challenges to solve with **both** PowerShell and Bash, with answer
keys.

## Related

- [Users and permissions](<users-and-permissions.md>) - why some commands need admin/sudo.
- [File systems](<file-systems.md>) - what's underneath these paths.
- [Process management](<process-management.md>) - more pipes and filters on running programs.
