"""
backup.py - full + incremental backups with SHA-256 manifests, verification, restore, and retention.

Layout of the backup store:
    <store>/20260304-020000-full/   files/...  manifest.json
    <store>/20260305-020000-incr/   files/...  manifest.json   (only changed/new files are copied)

Every manifest lists the COMPLETE state of the source at that moment: for each file its hash, size,
and which backup folder physically holds that version. So restoring any point in time = read one
manifest, copy each file from where it lives. (That's also why an incremental chain is only as good
as its oldest link - delete the full and every incremental after it is useless.)

Usage:
    python backup.py full    <source> <store>
    python backup.py incr    <source> <store>
    python backup.py list    <store>
    python backup.py verify  <store> [backup-name]          # re-hash stored files (detects bit rot/tampering)
    python backup.py restore <store> <backup-name|latest> <target>
    python backup.py prune   <store> --keep-chains 2        # retention: keep the last N full chains
"""

import argparse
import datetime as dt
import hashlib
import json
import shutil
import sys
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def backups(store: Path) -> list[Path]:
    return sorted(p for p in store.iterdir() if (p / "manifest.json").exists()) if store.exists() else []


def load_manifest(b: Path) -> dict:
    return json.loads((b / "manifest.json").read_text(encoding="utf-8"))


def run_backup(source: Path, store: Path, kind: str) -> None:
    if not source.is_dir():
        sys.exit(f"source {source} is not a folder")
    previous = backups(store)
    if kind == "incr" and not previous:
        print("No previous backup - an incremental needs a full to build on. Doing a full instead.")
        kind = "full"
    base = load_manifest(previous[-1])["files"] if kind == "incr" else {}

    name = f"{dt.datetime.now():%Y%m%d-%H%M%S}-{kind}"
    dest = store / name
    (dest / "files").mkdir(parents=True)

    files, copied, bytes_copied, unchanged = {}, 0, 0, 0
    for path in sorted(p for p in source.rglob("*") if p.is_file()):
        rel = path.relative_to(source).as_posix()
        st = path.stat()
        prev = base.get(rel)
        # Fast path: same size + mtime as last time -> assume unchanged (what most tools do);
        # otherwise hash it to be sure.
        if prev and prev["size"] == st.st_size and prev["mtime"] == st.st_mtime:
            files[rel] = prev
            unchanged += 1
            continue
        digest = sha256(path)
        if prev and prev["sha256"] == digest:
            files[rel] = {**prev, "mtime": st.st_mtime}
            unchanged += 1
            continue
        target = dest / "files" / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        files[rel] = {"sha256": digest, "size": st.st_size, "mtime": st.st_mtime, "stored_in": name}
        copied += 1
        bytes_copied += st.st_size

    deleted = sorted(set(base) - set(files))
    manifest = {"name": name, "type": kind, "source": str(source.resolve()),
                "created": dt.datetime.now().isoformat(timespec="seconds"),
                "based_on": previous[-1].name if kind == "incr" else None,
                "files": files, "deleted_since_previous": deleted}
    (dest / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print(f"{name}: {copied} file(s) copied ({bytes_copied:,} bytes), {unchanged} unchanged, "
          f"{len(deleted)} deleted since previous, {len(files)} total in this restore point")


def cmd_list(store: Path) -> None:
    print(f"{'BACKUP':<26}{'TYPE':<6}{'FILES':>7}{'STORED HERE':>13}  BASED ON")
    for b in backups(store):
        m = load_manifest(b)
        here = sum(1 for f in m["files"].values() if f["stored_in"] == m["name"])
        print(f"{m['name']:<26}{m['type']:<6}{len(m['files']):>7}{here:>13}  {m['based_on'] or '-'}")


def resolve_name(store: Path, name: str) -> Path:
    all_b = backups(store)
    if not all_b:
        sys.exit("no backups in store")
    if name == "latest":
        return all_b[-1]
    for b in all_b:
        if b.name == name:
            return b
    sys.exit(f"no backup named {name}")


def cmd_verify(store: Path, name: str | None) -> bool:
    targets = [resolve_name(store, name)] if name else backups(store)
    # One stored file can be referenced by many restore points (a full + every incremental after it),
    # so check each physical file once and report how many restore points depend on it.
    refs: dict[tuple[str, str], dict] = {}
    for b in targets:
        m = load_manifest(b)
        for rel, info in m["files"].items():
            entry = refs.setdefault((info["stored_in"], rel), {"sha256": info["sha256"], "used_by": []})
            entry["used_by"].append(m["name"])
    bad = 0
    for (stored_in, rel), entry in sorted(refs.items()):
        stored = store / stored_in / "files" / rel
        problem = "MISSING" if not stored.exists() else "CORRUPT" if sha256(stored) != entry["sha256"] else None
        if problem:
            bad += 1
            print(f"  {problem}  {rel} in {stored_in} - breaks {len(entry['used_by'])} restore point(s): "
                  f"{', '.join(entry['used_by'])}")
    print(f"Verified {len(refs)} stored file(s) used by {len(targets)} restore point(s): "
          f"{'all OK' if not bad else f'{bad} problem(s)'}")
    return bad == 0


def cmd_restore(store: Path, name: str, target: Path) -> None:
    b = resolve_name(store, name)
    m = load_manifest(b)
    if target.exists() and any(target.iterdir()):
        sys.exit(f"target {target} is not empty - restore to an empty folder, then compare/copy back "
                 "(never restore straight over the only copy)")
    ok = 0
    for rel, info in m["files"].items():
        src = store / info["stored_in"] / "files" / rel
        dst = target / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        if sha256(dst) == info["sha256"]:
            ok += 1
        else:
            print(f"  restored {rel} but hash does NOT match the manifest!")
    print(f"Restored {ok}/{len(m['files'])} files from {m['name']} into {target} - all verified by SHA-256"
          if ok == len(m["files"]) else f"Restored with {len(m['files']) - ok} verification failures")


def cmd_prune(store: Path, keep: int) -> None:
    all_b = backups(store)
    fulls = [i for i, b in enumerate(all_b) if load_manifest(b)["type"] == "full"]
    if len(fulls) <= keep:
        print(f"{len(fulls)} full chain(s) - nothing to prune (keeping {keep})")
        return
    cutoff = fulls[-keep]  # index of the oldest full we keep; everything before it goes
    for b in all_b[:cutoff]:
        shutil.rmtree(b)
        print(f"  pruned {b.name}")
    print("Note: we delete whole chains only - removing a full but keeping its incrementals would orphan them.")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    s = p.add_subparsers(dest="cmd", required=True)
    for k in ("full", "incr"):
        x = s.add_parser(k); x.add_argument("source", type=Path); x.add_argument("store", type=Path)
    x = s.add_parser("list"); x.add_argument("store", type=Path)
    x = s.add_parser("verify"); x.add_argument("store", type=Path); x.add_argument("name", nargs="?")
    x = s.add_parser("restore"); x.add_argument("store", type=Path); x.add_argument("name"); x.add_argument("target", type=Path)
    x = s.add_parser("prune"); x.add_argument("store", type=Path); x.add_argument("--keep-chains", type=int, default=2)
    a = p.parse_args()

    if a.cmd in ("full", "incr"):
        run_backup(a.source, a.store, a.cmd)
    elif a.cmd == "list":
        cmd_list(a.store)
    elif a.cmd == "verify":
        sys.exit(0 if cmd_verify(a.store, a.name) else 1)
    elif a.cmd == "restore":
        cmd_restore(a.store, a.name, a.target)
    elif a.cmd == "prune":
        cmd_prune(a.store, a.keep_chains)


if __name__ == "__main__":
    main()
