# Msla-imager

Shared code for the MSLA PCB imager (MSLA PRINTER Claude Project). One folder per lane; each lane writes only its own.

| Folder | Lane | What |
|---|---|---|
| `software/` | L4 Software | Pattern generator, Gerber-to-PNG converter, IF-13 job files; later the Pi app. See `software/README.md` |
| `firmware/` | L3 Controller and safety | Nano firmware (not started) |
| `calcs/` | HQ | imager-04 calc script (not started) |

Plan docs live in the Claude Project (imager-00 to imager-08, IF-13 spec). Run L4 tools from `software/`.
