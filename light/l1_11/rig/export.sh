#!/bin/sh
# L1: L1.11 rig export: every printable part to stl/, assembly views to PNG. Run from this folder: sh export.sh
# Needs OpenSCAD 2021.01 (xvfb-run for the PNGs on a headless box).
set -e
cd "$(dirname "$0")"
mkdir -p stl
for p in base rotor frame shaft knob scale track1 track2 carriage; do
  openscad -q --export-format=binstl -o "stl/l1_11_$p.stl" -D "part=\"$p\"" l1_11_rig.scad
  echo "stl/l1_11_$p.stl"
done
RUN=""
command -v xvfb-run >/dev/null 2>&1 && RUN="xvfb-run -a"
$RUN openscad -q -o l1_11_rig_assembly.png -D 'part="assembly"' --imgsize=1800,1000 \
  --camera=0,0,0,62,0,40,0 --viewall --autocenter --colorscheme=Tomorrow l1_11_rig.scad
echo done
