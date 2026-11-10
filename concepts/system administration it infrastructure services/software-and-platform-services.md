# Software & Platform Services

The services people actually *use*: email, productivity apps, file and print sharing, and the
platforms (web servers, databases) applications run on.

## Communication services

### Email

Three protocols, three jobs:

| Protocol | Port (plain / TLS) | Job |
|---|---|---|
| **SMTP** | 25 (server-to-server), **587** (client submission, STARTTLS), 465 (implicit TLS) | **sending** mail |
| **POP3** | 110 / **995** | **downloading** mail to one device (usually deletes from server) - old |
| **IMAP** | 143 / **993** | **syncing** mail - stays on the server, same view on every device |

```
Sender's client --SMTP--> sender's mail server --SMTP--> recipient's mail server (found via MX record)
                                                         <--IMAP-- recipient's phone/laptop
```

> 🖼️ **Image idea: email flow** - the path above with the protocol on each arrow and the DNS MX
> lookup shown as a side step.
> Suggested file: `assets/img/email-flow.png`
<!-- ![email flow](<../../assets/img/email-flow.png>) -->

Most organizations use hosted email (Microsoft 365 / Exchange Online, Google Workspace) instead
of running their own. Sysadmins still manage DNS records for it:

- **MX** - where mail for the domain goes.
- **SPF** (TXT) - which servers may send mail for the domain.
- **DKIM** (TXT) - public key used to verify the domain's mail signatures.
- **DMARC** (TXT) - what receivers should do when SPF/DKIM fail, and where to send reports.

### Chat, video, VoIP

Teams, Slack, Zoom, VoIP phones. Usually SaaS; tickets are mostly about accounts, audio devices,
network quality (VoIP/video need low latency and jitter → **QoS** on the network).

## User productivity services

Office suites, browsers, line-of-business apps.

- **Licensing** - per user, per device, subscription, concurrent. Track who has what; reclaim
  licenses from leavers.
- **Software policy** - which apps are approved; how users request others.
- Pay attention to **EULAs** - personal/home licenses usually can't be used commercially.

## Security services

- **HTTPS / TLS certificates** - any internal or public web service should use TLS. Certificates
  come from a **public CA** (e.g. Let's Encrypt, DigiCert) or an **internal CA** for internal-only
  services.
- **Certificates expire** - expired certificates are a classic "everything broke at midnight"
  outage. Monitor expiry dates (and automate renewal where possible).

## File services

Shared storage for teams.

| Protocol | Ecosystem | Notes |
|---|---|---|
| **SMB / CIFS** | Windows (and Samba on Linux/macOS) | TCP 445. Mapped drives (`\\fileserver\share`). Disable old SMBv1 (insecure). |
| **NFS** | Linux/Unix | mounting remote directories |
| Cloud file sync | OneDrive/SharePoint, Google Drive, Dropbox | SaaS replacement for many file servers |
| **NAS** | appliance | network storage box serving SMB/NFS |

```powershell
New-SmbShare -Name "Finance" -Path "D:\Shares\Finance" -FullAccess "CORP\Finance-Admins" -ChangeAccess "CORP\Finance"
net use F: \\fileserver01\Finance /persistent:yes
Get-SmbOpenFile                      # who has what open (on the server)
```

```bash
sudo mount -t cifs //fileserver01/Finance /mnt/finance -o username=amina
```

Remember: share permissions and NTFS permissions both apply - the most restrictive wins.

## Print services

- A **print server** (Windows Print Server, or **CUPS** on Linux/macOS) manages queues, drivers,
  and permissions centrally. Users connect to `\\printserver\HR-Printer` instead of each one
  installing drivers.
- Deploy printers via Group Policy / MDM.
- Classic fix: **restart the Print Spooler** service and clear stuck jobs
  (`C:\Windows\System32\spool\PRINTERS`).
- Give printers **DHCP reservations** so their IP never changes.

## Platform services

### Web servers

Software that serves websites/apps over HTTP(S): **Apache**, **Nginx**, **IIS** (Windows).

- Listen on port 80/443; serve files or forward requests to an application (**reverse proxy**).
- Config files: `/etc/nginx/`, `/etc/apache2/`; IIS Manager on Windows.
- Logs: access log (every request) and error log - first place to look when a site breaks.

### Database servers

Store and query structured data: **MySQL/MariaDB**, **PostgreSQL**, **Microsoft SQL Server**,
plus NoSQL (MongoDB). Sysadmin concerns: backups, access control, performance, patching.
Database ports should **never** be exposed to the internet.

## Troubleshooting platform services

### HTTP status codes

| Range | Meaning | Common ones |
|---|---|---|
| 2xx | success | 200 OK |
| 3xx | redirect | 301 moved permanently, 302 found, 304 not modified |
| 4xx | **client** error - the request was wrong | 400 bad request, 401 unauthenticated, 403 forbidden, 404 not found, 429 too many requests |
| 5xx | **server** error - the server failed | 500 internal error, 502 bad gateway (upstream app down behind a proxy), 503 unavailable, 504 gateway timeout |

```bash
curl -I https://intranet.example.com         # just the headers + status code
curl -v https://intranet.example.com         # full handshake + headers (TLS problems show here)
```

```powershell
Invoke-WebRequest https://intranet.example.com -Method Head | Select-Object StatusCode
```

Method: is the **server** up (ping/port check) → is the **service** listening (port 443) → what
does the **app** return (status code) → what does the **log** say.

## Managing cloud services

With SaaS, you don't patch servers, but you still manage:

- **Users, licenses, and permissions** in an admin console.
- **Configuration** (security settings, sharing policies, retention).
- **Backups** - the provider keeps the service running; protecting *your data* from deletion
  or ransomware is still your job under the **shared responsibility model**.
- **Vendor status pages** - check them first during "is it just us?" outages.

## Practice project

[`practice/system-administration-it-infrastructure-services/service-health-monitor`](<../../practice/system-administration-it-infrastructure-services/service-health-monitor>) -
a config-driven monitor that checks a list of services (HTTP status + response time, TCP ports
like SMTP 587 / IMAP 993 / SMB 445, and **TLS certificate expiry days**) and prints a status
board - a tiny version of tools like Uptime Kuma or Nagios. Includes a local test web server so
you can watch it go red and green.

## Related

- [Network and infrastructure services](<network-and-infrastructure-services.md>) - DNS/DHCP/NTP these depend on.
- [Pelcgbybtl (cryptology)](<../it security/pelcgbybtl-cryptology.md>) - how TLS certificates work.
- [The transport and application layers](<../computer networking/the-transport-and-application-layers.md>) - port numbers.
