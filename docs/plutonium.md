# Plutonium files (NOT part of the original game)

What "compatible with Plutonium's game files" can mean for this port, and what it cannot.

## What was checked (public Plutonium guides)

* Plutonium's T5 (Black Ops) client needs a Steam copy of the game; its setup asks for the Steam folder
  (`...\steamapps\common\Call of Duty Black Ops`). It does not ship the game files.
* Plutonium keeps its own data in `%LOCALAPPDATA%\Plutonium\storage\t5` (T4 and T6 have `mods` and `scripts` folders
  there; the T5 `mods` folder is assumed to match, not confirmed).

## What this means here

| Plutonium side | This port |
| --- | --- |
| The Steam game folder | The same folder the port needs (README, "Copy the game files"). Nothing to convert. `python3 tools/native/import-plutonium.py --check-game <game>` checks it. |
| `storage/t5/mods/<name>` | The port loads `<game>/mods/<name>/` (`mod.ff`, `.iwd`, ...). `import-plutonium.py` copies and reports what each folder holds. |
| Loose `.gsc` scripts that Plutonium loads from its own folder | Not loaded by this port by itself. Inside a mod folder a `.gsc` goes through the engine's file system and may load when a script calls it; untested. |
| Plutonium's client, accounts, servers, anti-cheat, extra script functions | Not included and not needed. Not implemented. |

## Use

```
python3 tools/native/import-plutonium.py "%LOCALAPPDATA%\Plutonium" --out game --dry-run   # report only
python3 tools/native/import-plutonium.py "%LOCALAPPDATA%\Plutonium" --out game
```

Then copy `game/mods/<name>` to the device (`files/game/mods/<name>/` on Android) and choose it on Settings > EXTRAS >
MOD, or set `+set fs_game mods/<name>`. A mod folder name should be letters, digits and `_`.

Limits: a mod built for Plutonium's own extended script functions may fail at its first call to one. No mod has been
run through this tool on a device yet; `tools/native/test-plutonium.sh` tests the copy and the report on the build
host.
