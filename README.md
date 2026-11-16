# Msla-imager

Shared code for the MSLA PCB imager (MSLA PRINTER Claude Project). This index is kept by HQ, in step with the Code home section of imager-00.

- **Folders.** Each folder belongs to one lane, except `calcs/`, where any lane adds its own calc scripts as separate files.
- **One writer per file.** The lane that creates a file owns it and names itself on line 1, or on line 2 under a shebang; other lanes change it through that owner.
- **Commits** start with the package or lane (`L4.2: loader`, `L4: converter v0`). A packet that confirms code cites the commit.

| Folder | Lane | What |
|---|---|---|
| `calcs/` | HQ, plus lane-owned scripts | `imager_calcs.py` (HQ, recovery pending). Lane scripts: `l1_*` (L1 Light engine), `l2_*` (L2 LCD mask) |
| `light/` | L1 Light engine | Cluster and sink board KiCad, stand mounts (not started) |
| `lcd/` | L2 LCD mask | Pi video config and bring-up scripts (`setup_display.sh`, `fbtest.py`, `show_png.py`, `edid_timing.py`; simulation-checked), the 1:1 PNG script until L4 takes it, package records in `lcd/records/` |
| `software/` | L4 Software | Pattern generator, Gerber-to-PNG converter, IF-13 job files; later the Pi app. See `software/README.md` |
| `firmware/` | L3 Controller and safety | Nano firmware (not started) |
| `mech/` | L5 Mechanics | Platen and enclosure CAD, 3018 G-code (not started) |

Plan docs live in the Claude Project (imager-00 to imager-09, IF-13 spec). Run L4 tools from `software/`. Datasheets under copyright (the Sharp LS055R1SX04 spec, for one) stay out of this repo.
