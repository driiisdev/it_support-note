# Data Classification & Handling (template)

> Four levels is enough for most organizations. If people can't classify something in 10 seconds,
> the scheme is too complicated.

| Level | Examples | Who can access | Storage | Sharing externally | Disposal |
|---|---|---|---|---|---|
| **Public** | website content, press releases, job ads | anyone | anywhere | freely | normal |
| **Internal** | org charts, internal procedures, most email | employees & contractors | company systems | only with a business need | normal delete |
| **Confidential** | contracts, customer lists, financials, source code | named teams (need-to-know) | approved company systems, encrypted devices | only via approved secure sharing, with NDA | secure delete / shred |
| **Restricted** | personal data (HR, health, ID numbers), payment card data, passwords/keys, M&A | small named group, access logged & reviewed | restricted locations only; encrypted at rest and in transit | only with Data Owner approval + encryption | certified destruction (wipe/purge or physical) |

## Rules that apply to everything

- **The data owner** (usually the business, not IT) decides the classification and approves access.
- When unsure, treat it as the **higher** level.
- Label documents (header/footer, or sensitivity labels in Microsoft 365).
- Access to Confidential and Restricted data is **reviewed every 6 months** - remove people who no
  longer need it.

## Device disposal

| Media | Method |
|---|---|
| HDD | overwrite (NIST 800-88 "clear/purge") or degauss/shred if failed |
| SSD / NVMe | built-in secure erase / crypto-erase (destroy the encryption key), or shred |
| Phones / tablets | encrypted by default → factory reset (crypto-erase) |
| Paper | cross-cut shredder or locked confidential-waste bin |

Record each disposal (asset tag, method, date, who, certificate number) - see the asset inventory in
[it-asset-runbook](../../../system-administration-it-infrastructure-services/it-asset-runbook).
