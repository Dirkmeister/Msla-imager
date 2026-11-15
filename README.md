# Msla-imager

Shared code for the MSLA PCB imager (MSLA PRINTER Claude Project). This index is kept by HQ, in step with the Code home section of imager-00.

- **Folders.** Each folder belongs to one lane, except `calcs/`, where any lane adds its own calc scripts as separate files.
- **One writer per file.** The lane that creates a file owns it and names itself on the file's first line; other lanes change it through that owner.
- **Commits** start with the lane (`L4: converter v0`). A packet that confirms code cites the commit.

| Folder | Lane | What |
|---|---|---|
| `software/` | L4 Software | Pattern generator, Gerber-to-PNG converter, IF-13 job files; later the Pi app. See `software/README.md` |
| `firmware/` | L3 Controller and safety | Nano firmware (not started) |
| `lcd/` | L2 LCD mask | Pi video config, bring-up scripts, the 1:1 PNG script until L4 takes it (not started) |
| `mech/` | L5 Mechanics | Platen and enclosure CAD, 3018 G-code (not started) |
| `calcs/` | HQ, plus lane-owned scripts | `imager_calcs.py` (HQ, recovery pending); lanes add their own calc scripts, one owner per file (not started) |

Plan docs live in the Claude Project (imager-00 to imager-08, IF-13 spec). Run L4 tools from `software/`.
