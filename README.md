# EngineMods — mod repository for ii Engine

This repo is the **live mod catalog** that ii Engine reads:

- `catalog.json` — the list shown in the app's **Mod Library** (Trusted + Community tabs)
- `mods/` — the mod DLL files themselves

The app fetches `catalog.json` from
`https://raw.githubusercontent.com/ItzGameDev/EngineMods/main/catalog.json`
and downloads files straight from `mods/`. Because it's a live fetch, **you can
add or remove mods without rebuilding the exe** — changes appear within about a
minute (or on app restart).

## Add a mod

```powershell
python add_mod.py C:\path\to\MyMod.dll --name "My Mod" --description "What the mod does"
```

- Trusted tab is the default; add `--community` to list it under Community instead.
- The script copies the DLL into `mods/`, computes its SHA-256 and byte size
  (ii Engine verifies the hash when a player installs), and appends an entry to
  `catalog.json`.
- Optional: `--author "YourName"`, `--thumb https://.../pic.png`, `--force` to
  replace an existing id, `--id custom-id`.

### Publish

```powershell
git add .
git commit -m "add MyMod"
git push
```

Or drag-and-drop the changed files on the GitHub page:
<https://github.com/ItzGameDev/EngineMods>

## Entry format (manual editing)

```json
{
  "id": "my-mod",
  "name": "My Mod",
  "description": "What the mod does",
  "filename": "MyMod.dll",
  "sha256": "<64 hex chars of the exact file bytes>",
  "byte_size": 12345,
  "download_url": "https://raw.githubusercontent.com/ItzGameDev/EngineMods/main/mods/MyMod.dll",
  "author": { "id": "itzgame", "display_name": "ItzGame", "avatar": null }
}
```

Entries missing `id`/`name`/`filename`/`sha256` are ignored by the app
(defensive validation), and `download_url` defaults to `mods/<filename>` if
omitted.

## Notes

- The repo must stay **public** — the app reads it through raw.githubusercontent.com.
- `sha256` must match the uploaded file exactly, or the app refuses to install it.
- Only add mods you have the right to distribute.
