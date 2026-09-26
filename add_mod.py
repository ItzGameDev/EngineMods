#!/usr/bin/env python3
"""Register a mod DLL in the EngineMods catalog for ii Engine.

Usage:
  python add_mod.py C:\\path\\to\\MyMod.dll --name "My Mod" --description "What it does"
  python add_mod.py MyMod.dll -n "My Mod" -d "..." --author "ItzGame"
  python add_mod.py MyMod.dll -n "My Mod" -d "..." --community
  python add_mod.py MyMod.dll -n "My Mod" -d "..." --force      # replace existing id

What it does:
  1. copies the DLL into ./mods/
  2. computes its SHA-256 and byte size (ii Engine verifies the hash on install)
  3. appends an entry to ./catalog.json (Trusted tab by default, --community for Community)
  4. prints the entry it wrote

Publish (from this folder):
  git add .
  git commit -m "add MyMod"
  git push
or drag-and-drop the changed files on https://github.com/ItzGameDev/EngineMods

The app reads catalog.json from
https://raw.githubusercontent.com/ItzGameDev/EngineMods/main/catalog.json
(changes show up within about a minute, or on app restart).
"""
import argparse
import hashlib
import json
import re
import shutil
import sys
from datetime import date
from pathlib import Path
from urllib.parse import quote

REPO = "ItzGameDev/EngineMods"
BRANCH = "main"
ROOT = Path(__file__).resolve().parent
CATALOG = ROOT / "catalog.json"
MODS = ROOT / "mods"


def slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s or "mod"


def main() -> None:
    ap = argparse.ArgumentParser(description="Add a mod DLL to catalog.json")
    ap.add_argument("dll", help="path to the .dll file")
    ap.add_argument("-n", "--name", required=True, help="display name in the Mod Library")
    ap.add_argument("-d", "--description", default="", help="one-line description (tags are derived from it)")
    ap.add_argument("--author", default="ItzGame", help="creator display name")
    ap.add_argument("--community", action="store_true", help="list under Community instead of Trusted")
    ap.add_argument("--id", default=None, help="custom id (default: slug of the name)")
    ap.add_argument("--thumb", default=None, help="optional https:// URL of a thumbnail image")
    ap.add_argument("--force", action="store_true", help="replace an entry that already has this id")
    args = ap.parse_args()

    src = Path(args.dll)
    if not src.is_file():
        sys.exit(f"error: file not found: {src}")

    data = src.read_bytes()
    if not data:
        sys.exit(f"error: {src} is empty")
    sha = hashlib.sha256(data).hexdigest()
    filename = src.name

    if CATALOG.exists():
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    else:
        catalog = {"schema": 1, "trusted": [], "community": []}
    trusted = catalog.setdefault("trusted", [])
    community = catalog.setdefault("community", [])

    mod_id = args.id or slug(args.name)

    def find(bucket):
        return next((i for i, m in enumerate(bucket) if m.get("id") == mod_id), None)

    hit_t, hit_c = find(trusted), find(community)
    if (hit_t is not None or hit_c is not None) and not args.force:
        sys.exit(f"error: id {mod_id!r} is already in the catalog (use --force to replace it)")

    MODS.mkdir(exist_ok=True)
    dest = MODS / filename
    if src.resolve() != dest.resolve():
        shutil.copyfile(src, dest)

    entry = {
        "id": mod_id,
        "name": args.name,
        "description": args.description,
        "filename": filename,
        "sha256": sha,
        "byte_size": len(data),
        "download_url": f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/mods/{quote(filename)}",
        "author": {
            "id": slug(args.author),
            "display_name": args.author,
            "avatar": None,
            "role_name": "Creator",
            "role_color": "#6d9afb",
        },
    }
    if args.thumb:
        entry["thumbnail_url"] = args.thumb

    if args.community:
        if hit_c is not None:
            community[hit_c] = entry
        else:
            if hit_t is not None:
                trusted.pop(hit_t)  # moved tab
            community.append(entry)
        bucket_name = "community"
    else:
        if hit_t is not None:
            trusted[hit_t] = entry
        else:
            if hit_c is not None:
                community.pop(hit_c)  # moved tab
            trusted.append(entry)
        bucket_name = "trusted"

    catalog["updated_at"] = date.today().isoformat()
    CATALOG.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")

    print(f"OK  {mod_id} -> {bucket_name} tab")
    print(f"    file   mods/{filename}")
    print(f"    size   {len(data)} bytes")
    print(f"    sha256 {sha}")
    print()
    print(json.dumps(entry, indent=2))
    print()
    print("Next: upload the changes so players get them:")
    print("  git add .")
    print(f'  git commit -m "add {mod_id}"')
    print("  git push")


if __name__ == "__main__":
    main()
