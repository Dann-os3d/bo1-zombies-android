#!/usr/bin/env python3
"""import-plutonium.py - bring mods from a Plutonium T5 folder into this port's game folder.

Plutonium keeps its own data in  %LOCALAPPDATA%\\Plutonium\\storage\\t5  (mods in its "mods" subfolder).
This port loads mods from  <game>/mods/<name>/  (docs/android-port.md, "Mods and custom maps"), so the step is a copy
into that layout plus a check of what the folder holds. Nothing of Plutonium itself (its client, accounts, servers)
is read or needed. Host-side tool: Python 3, no packages.

  python3 import-plutonium.py <plutonium-folder> --out <game-folder> [--dry-run]
  python3 import-plutonium.py --check-game <game-folder>

<plutonium-folder> may be the Plutonium folder, storage/t5, or the mods folder itself.
Exit status: 0 done, 1 nothing imported or the game folder is wrong, 2 usage.
"""
import argparse
import os
import re
import shutil
import sys

NAME_OK = re.compile(r"^[A-Za-z0-9_]+$")   # what fs_mods accepts (com_files.cpp, FS_ModStackParse)


def find_mods_dir(src):
    for sub in (("mods",), ("storage", "t5", "mods"), ("t5", "mods")):
        c = os.path.join(src, *sub)
        if os.path.isdir(c):
            return c
    return src if os.path.isdir(src) else None


def scan_mod(path):
    info = {"files": 0, "bytes": 0, "ff": 0, "iwd": 0, "gsc": 0, "mod_ff": False}
    for root, _dirs, files in os.walk(path):
        for f in files:
            info["files"] += 1
            try:
                info["bytes"] += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
            low = f.lower()
            if low.endswith(".ff"):
                info["ff"] += 1
                if low == "mod.ff":
                    info["mod_ff"] = True
            elif low.endswith(".iwd"):
                info["iwd"] += 1
            elif low.endswith(".gsc"):
                info["gsc"] += 1
    return info


def notes_for(name, info):
    notes = []
    if not NAME_OK.match(name):
        notes.append("name has characters other than letters, digits and '_': rename the folder (fs_mods skips such names)")
    if info["files"] == 0:
        notes.append("empty folder")
    elif info["ff"] == 0 and info["iwd"] == 0:
        notes.append("no .ff or .iwd: a script-only mod; Plutonium loads loose scripts from its own folder, this port does not "
                     "load them by itself (a .gsc here is read only when a script of the mod calls it; untested)")
    elif info["ff"] and not info["mod_ff"]:
        notes.append("fastfiles but no mod.ff: loads only if they are named after the map (docs/android-port.md)")
    elif info["gsc"]:
        notes.append("%d loose .gsc next to the fastfiles: kept; untested here" % info["gsc"])
    return notes


def fmt_size(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return "%.0f %s" % (n, unit) if unit == "B" else "%.1f %s" % (n, unit)
        n /= 1024.0


def import_mods(src, out, dry_run):
    mods_dir = find_mods_dir(src)
    if not mods_dir:
        print("error: %s is not a folder" % src)
        return 1
    names = sorted(d for d in os.listdir(mods_dir) if os.path.isdir(os.path.join(mods_dir, d)))
    if not names:
        print("nothing to import: no mod folders in %s" % mods_dir)
        return 1
    done = 0
    for name in names:
        path = os.path.join(mods_dir, name)
        info = scan_mod(path)
        dst = os.path.join(out, "mods", name)
        print("%s: %d files, %s, %d fastfile(s), %d iwd" % (name, info["files"], fmt_size(info["bytes"]), info["ff"], info["iwd"]))
        for n in notes_for(name, info):
            print("  note: " + n)
        if info["files"] == 0:
            continue
        if dry_run:
            print("  would copy to %s" % dst)
        else:
            shutil.copytree(path, dst, dirs_exist_ok=True)
            print("  copied to %s" % dst)
        done += 1
    print("%s %d of %d mod folder(s)" % ("would import" if dry_run else "imported", done, len(names)))
    return 0 if done else 1


def check_game(game):
    ok = True
    if not os.path.isdir(game):
        print("error: %s is not a folder" % game)
        return 1
    zone = os.path.join(game, "zone")
    ffs = 0
    for root, _d, files in os.walk(zone):
        ffs += sum(1 for f in files if f.lower().endswith(".ff"))
    if ffs == 0:
        print("missing: zone/ with .ff files (copy the contents of the Steam folder, the one Plutonium's setup points at)")
        ok = False
    else:
        print("zone/: %d fastfiles" % ffs)
    if not os.path.isfile(os.path.join(game, "localization.txt")):
        print("missing: localization.txt (the app reports 'Game files not found' without it)")
        ok = False
    for d in os.listdir(game):
        if d.lower().startswith("call of duty") and os.path.isdir(os.path.join(game, d)):
            print("wrong: a nested '%s' folder; copy its contents one level up" % d)
            ok = False
    print("game folder looks right" if ok else "game folder needs fixing")
    return 0 if ok else 1


def main(argv):
    ap = argparse.ArgumentParser(description="Import Plutonium T5 mods into this port's game folder")
    ap.add_argument("source", nargs="?", help="Plutonium folder, storage/t5, or its mods folder")
    ap.add_argument("--out", default="game", help="the port's game folder (default ./game)")
    ap.add_argument("--dry-run", action="store_true", help="report only, copy nothing")
    ap.add_argument("--check-game", metavar="DIR", help="check a game folder instead of importing")
    a = ap.parse_args(argv)
    if a.check_game:
        return check_game(a.check_game)
    if not a.source:
        ap.print_usage()
        return 2
    return import_mods(a.source, a.out, a.dry_run)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
