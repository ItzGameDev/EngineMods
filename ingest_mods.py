#!/usr/bin/env python3
"""Drop-folder ingester for the EngineMods repository.

Drop mod DLLs into the drop folder and run this script; it registers them in
catalog.json, commits, and (by default) tries to push to GitHub.

Usage:
  python ingest_mods.py                 # ingest pending DLLs + commit + try push
  python ingest_mods.py --watch         # keep watching the drop folder
  python ingest_mods.py --trusted       # Trusted tab (default is Community)
  python ingest_mods.py --no-push       # register + commit only
  python ingest_mods.py --rebuild       # rebuild the exe so the offline seed
                                        # picks the new mods up (close the app)

Sidecar description: a text file with the same base name as the DLL
(MyMod.dll -> MyMod.txt) becomes the catalog description.

Files are moved to <drop>/done/ after a successful ingest, so each file is
processed once. Re-drop a file to update its entry (existing ids are
overwritten with --force, which keeps sha256 in sync after a rebuild).
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent          # .../@here/mod-repo
WORKSPACE = REPO.parent                         # .../@here
DROP = Path(r"C:\Users\saied\Downloads\mod-drop")
DONE = DROP / "done"
ADD_MOD = REPO / "add_mod.py"
DEFAULT_TAB = "community"


def prettify(stem: str) -> str:
    s = re.sub(r"[_\-]+", " ", stem)
    s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", s)
    return re.sub(r"\s+", " ", s).strip() or stem


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "mod"


def run(cmd, cwd, timeout=120, env=None):
    return subprocess.run(cmd, cwd=str(cwd), timeout=timeout,
                          capture_output=True, text=True, env=env)


def ingest_once(tab: str) -> list:
    DROP.mkdir(parents=True, exist_ok=True)
    DONE.mkdir(parents=True, exist_ok=True)
    dlls = sorted(p for p in DROP.glob("*.dll") if p.is_file())
    if not dlls:
        return []
    ingested = []
    for dll in dlls:
        stem = dll.stem
        name = prettify(stem)
        sidecar = dll.with_suffix(".txt")
        if sidecar.is_file():
            desc = sidecar.read_text(encoding="utf-8", errors="replace").strip()
        else:
            desc = (f"{name} - community mod added through the drop folder; "
                    f"no description provided yet.")
        cmd = [sys.executable, str(ADD_MOD), str(dll),
               "-n", name, "-d", desc, "--id", slug(stem), "--force"]
        if tab != "trusted":
            cmd.append("--community")
        r = run(cmd, cwd=REPO)
        if r.returncode != 0:
            print(f"SKIP {dll.name}: {(r.stdout + r.stderr).strip()}")
            continue
        print((r.stdout or "").strip())
        shutil.move(str(dll), str(DONE / dll.name))
        if sidecar.is_file():
            shutil.move(str(sidecar), str(DONE / sidecar.name))
        ingested.append(name)
    return ingested


def git(args, timeout=120, env=None):
    return run(["git", *args], cwd=REPO, timeout=timeout, env=env)


def commit(names: list) -> bool:
    if git(["add", "-A"]).returncode != 0:
        print("git add failed")
        return False
    if not git(["status", "--porcelain"]).stdout.strip():
        print("catalog unchanged - nothing to commit")
        return True
    msg = "ingest: " + ", ".join(names) if names else "ingest: catalog update"
    r = git(["commit", "-m", msg])
    if r.returncode != 0:
        print("git commit failed:\n" + (r.stdout + r.stderr).strip())
        return False
    print((r.stdout or "").strip())
    return True


def push() -> bool:
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    try:
        r = git(["push", "origin", "main"], timeout=45, env=env)
    except subprocess.TimeoutExpired:
        print("push timed out - a sign-in window may be waiting for you "
              "(or run with --no-push)")
        return False
    if r.returncode != 0:
        print("push failed (not signed in yet?):")
        print("  " + (r.stderr or r.stdout).strip().splitlines()[-1])
        print("  Options: click the GitHub sign-in window if one appeared,")
        print("  run 'git push' yourself once, or drag-and-drop the changed")
        print("  files on https://github.com/ItzGameDev/EngineMods")
        return False
    print("pushed to https://github.com/ItzGameDev/EngineMods")
    return True


def rebuild() -> bool:
    steps = [
        [sys.executable, "extract_frontend.py"],
        [sys.executable, "patch_offline.py"],
        [sys.executable, str(WORKSPACE / ".tools" / "check_patch_markers.py")],
        [sys.executable, "verify.py"],
        ["node", str(WORKSPACE / ".tools" / "test_fixture.cjs")],
        [sys.executable, "patch_exe.py"],
    ]
    for cmd in steps:
        r = run(cmd, cwd=REPO.parent / "recovered", timeout=600)
        tail = "\n".join((r.stdout or "").strip().splitlines()[-4:])
        if r.returncode != 0:
            print(f"rebuild step failed: {cmd}\n{(r.stdout + r.stderr)[-2000:]}")
            print("Hint: close ii-engine-offline.exe before --rebuild "
                  "(the exe is locked while it runs).")
            return False
        print(f"ok: {cmd[-1]} -> {tail.splitlines()[-1] if tail else ''}")
    print("rebuilt: offline seed now mirrors catalog.json")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="Ingest dropped mod DLLs into the repo")
    ap.add_argument("--watch", action="store_true",
                    help="keep running and ingest as files appear")
    ap.add_argument("--trusted", action="store_true",
                    help="list under the Trusted tab (default: community)")
    ap.add_argument("--no-push", action="store_true", help="skip the git push")
    ap.add_argument("--rebuild", action="store_true",
                    help="rebuild the exe so the offline seed picks mods up "
                         "(close the app first)")
    args = ap.parse_args()

    if not ADD_MOD.is_file():
        sys.exit(f"error: {ADD_MOD} not found")
    tab = "trusted" if args.trusted else DEFAULT_TAB

    def cycle() -> None:
        names = ingest_once(tab)
        if names:
            if commit(names) and not args.no_push:
                push()
            if args.rebuild and names:
                rebuild()

    if args.watch:
        print(f"watching {DROP} (Ctrl+C to stop)")
        try:
            while True:
                cycle()
                time.sleep(4)
        except KeyboardInterrupt:
            print("\nstopped")
    else:
        cycle()


if __name__ == "__main__":
    main()
