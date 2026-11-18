// L1: L1.11 rotation rig for the C optic test (T-UV-7, T-UV-6): base, rotor, frame with top arm, shaft, knob, lid scale, track (2 segments), detector carriage. OpenSCAD 2021.01. Export: light/l1_11/rig/export.sh
//
// World frame (mm): z up; origin on the rotation axis at the base's top face; the beam at 0 deg runs along +x.
// The axis passes through the center optic's exit face; the test board's front face sits h_exit behind it.
// The board (light/l1_11/test_board) bolts to the frame through its 71.0 mm hole square, so it mounts at
// 0 or 90 deg for the two axes of the 3528. The knob on the lid turns the rotor; the detector carriage
// locks into detents at 4, 12 and 18 in from the axis.
// Not in this file yet: the optic holder, blanks and shims. They need the optic's measured profile (no
// public 20XPS drawing), and get drawn when the optics land. h_exit is EST until then; the frame's foot
// slots take +-12 mm of it.
// Printer: Prusa MK3S+, 250 x 210 x 210 mm. Every part fits under 240 x 200 mm.

part = "assembly";
$fn = 72;
inch = 25.4;
FONT = "DejaVu Sans:style=Bold";

// ---- inputs ----
h_exit = 10.0;      // board front face to the optic exit face (EST until the optic is measured)
H      = 62.0;      // center LED height above the base's top face
box_h  = 254.0;     // shroud inside height, floor to lid: 10 in prints the longest shaft; cut it to
                    // L = (inside height) + (lid thickness) - 99 mm, from the top end
lid_t  = 5.0;       // lid thickness at the shaft hole (EST)

// test board and ATS
bt = 1.6;  bw = 86;  bh = 80;  hole_c = 35.5;  ats = 60;  ats_h = 25;
x_bf = -h_exit;  x_bb = x_bf - bt;      // board front and back faces

// fasteners: ISO M3 nut 5.5 across flats, 2.4 thick; pockets with clearance
m3 = 3.4;  m3_tap = 2.8;  nut_af = 5.7;  nut_t = 2.7;
module nut_trap(depth = nut_t) { cylinder(d = nut_af / cos(30), h = depth, $fn = 6); }

// base and rotor
base_t = 8;  base_w = 150;  boss_d = 20;  boss_h = 6;  clr = 0.3;
step_x = 58;                 // the base top steps down to the track flange level from here to its +x edge
rot_d = 140;  rot_t = 8;
foot_hole = [5, 30];         // rotor holes for the frame foot: x, +-y

// frame
fr_t = 6;  fr_w = 100;  fr_top = H + 45;  open_s = 61.2;
foot_t = 6;  foot_len = 40;  slot_len = 24;
arm_t = 12;  arm_w = 20;  arm_x1 = 10;  sock = 10.5;  sock_d = 10;

// shaft, knob, lid scale
shaft_s = 10.0;
shaft_z0 = fr_top + arm_t - sock_d;                    // shaft bottom, seated in the arm socket
knob_z0  = box_h - base_t + lid_t + 3;                  // knob skirt bottom, 3 mm over the lid (scale disk 2 mm)
knob_sock = 15;
shaft_len = knob_z0 + knob_sock - shaft_z0;
lid_hole = 36;

// track: flange z -8..-2, dovetail rib z -2..4
fl_t = 6;  fl_w = 44;  rib_b = 10;  rib_top = 14;  rib_h = 6;
z_fl = -base_t;  z_ft = z_fl + fl_t;  z_rt = z_ft + rib_h;
seg = [[75, 285], [285, 495]];
det = [4 * inch, 12 * inch, 18 * inch];
tab_len = 16;  tab_root = 8;  tab_tip = 11;  tab_y = 14;  tab_clr = 0.2;

// detector carriage (detector board: light/l1_11/test_board board C, LED 12 mm above its two M3 holes 12 mm apart)
car_back = 26;  car_front = 4;  car_w = 40;  car_top = 10;
post_t = 6;  post_w = 30;  post_top = H + 18;
det_led_above_holes = 12;  det_hole_dy = 6;

echo(str("shaft_len = ", shaft_len, " mm for box_h = ", box_h, " mm"));

// dovetail tab in 2D: root at x = 0, tip at x = -tab_len (pointing -x), centred on y = 0
module tab2d(socket = false) {
    c = socket ? tab_clr : 0;
    polygon([[c + (socket ? 1 : 0), -tab_root / 2 - c], [c + (socket ? 1 : 0), tab_root / 2 + c],
             [-tab_len - c, tab_tip / 2 + c], [-tab_len - c, -tab_tip / 2 - c]]);
}

module rib_profile() { polygon([[-rib_b / 2, 0], [rib_b / 2, 0], [rib_top / 2, rib_h], [-rib_top / 2, rib_h]]); }

// ---------------------------------------------------------------- parts
module base() {
    difference() {
        union() {
            translate([-base_w / 2, -base_w / 2, -base_t]) cube([step_x + base_w / 2, base_w, base_t]);
            translate([step_x, -base_w / 2, -base_t]) cube([base_w / 2 - step_x, base_w, fl_t]);
            cylinder(d = boss_d, h = boss_h);
            // index at 0 deg, pointing at the rotor rim
            translate([rot_d / 2 + 0.8, 0, z_ft]) linear_extrude(2.8) polygon([[0, 0], [3.5, -2.5], [3.5, 2.5]]);
        }
        for (s = [-1, 1]) translate([base_w / 2, s * tab_y, -base_t - 1]) linear_extrude(fl_t + 2) tab2d(true);
        // weight relief underneath, away from the boss
        for (sx = [-1, 1], sy = [-1, 1]) translate([sx * 33 - 15, sy * 33 - 15, -base_t - 0.01]) cube([30, 30, 4]);
    }
}

module rotor() {
    difference() {
        cylinder(d = rot_d, h = rot_t, $fn = 180);
        translate([0, 0, -0.01]) cylinder(d = boss_d + 2 * clr, h = boss_h + 0.4);
        for (s = [-1, 1]) translate([foot_hole[0], s * foot_hole[1], -0.01]) {
            cylinder(d = m3, h = rot_t + 1);
            nut_trap();
        }
        // rim ticks every 5 deg, longer every 10, engraved 0.6 deep; 0 deg = board normal = +x
        for (a = [0 : 5 : 355]) rotate(a) translate([rot_d / 2 - (a % 10 == 0 ? 8 : 5), -0.4, rot_t - 0.6]) cube([10, 0.8, 1]);
        translate([rot_d / 2 - 13, 0, rot_t - 0.6]) linear_extrude(1) text("0", size = 4, font = FONT, halign = "center", valign = "center");
    }
}

module frame() {
    xb = x_bb - fr_t;    // frame back face
    difference() {
        union() {
            translate([xb, -fr_w / 2, rot_t]) cube([fr_t, fr_w, fr_top - rot_t]);              // upright behind the board
            translate([xb, -fr_w / 2, rot_t]) cube([foot_len, fr_w, foot_t]);                  // foot, forward under the board
            for (y0 = [46, -50]) hull() {                                                       // gussets outside the board
                translate([x_bb, y0, rot_t + foot_t]) cube([0.01, 4, 25]);
                translate([x_bb, y0, rot_t + foot_t]) cube([25, 4, 0.01]);
            }
            translate([xb, -arm_w / 2, fr_top]) cube([arm_x1 - xb, arm_w, arm_t]);             // top arm to the axis
        }
        translate([xb - 1, -open_s / 2, H - open_s / 2]) cube([fr_t + 2, open_s, open_s]);     // ATS passes through
        for (sy = [-1, 1], sz = [-1, 1]) translate([xb - 0.01, sy * hole_c, H + sz * hole_c]) rotate([0, 90, 0]) {
            cylinder(d = m3, h = fr_t + 1);                                                     // board corner holes
            nut_trap();                                                                         // nuts on the back face
        }
        for (s = [-1, 1]) hull() for (dx = [-slot_len / 2, slot_len / 2])                        // foot slots: h_exit adjust
            translate([foot_hole[0] + dx, s * foot_hole[1], rot_t - 1]) cylinder(d = m3, h = foot_t + 2);
        translate([-sock / 2, -sock / 2, fr_top + arm_t - sock_d]) cube([sock, sock, sock_d + 1]);   // shaft socket
        translate([0, -arm_w, fr_top + arm_t - sock_d / 2]) rotate([-90, 0, 0]) cylinder(d = m3, h = 2 * arm_w);
    }
}

module shaft() {
    difference() {
        translate([-shaft_s / 2, -shaft_s / 2, 0]) cube([shaft_s, shaft_s, shaft_len]);
        translate([0, -shaft_s, sock_d / 2]) rotate([-90, 0, 0]) cylinder(d = m3_tap, h = 2 * shaft_s);   // pin threads in
    }
}

module knob() {
    difference() {
        union() {
            cylinder(d = 60, h = 2.4);                                                         // skirt over the lid hole
            cylinder(d = 44, h = 18);                                                          // grip
            linear_extrude(2.4) polygon([[26, -3], [68, -0.4], [68, 0.4], [26, 3]]);           // pointer over the ticks
        }
        for (a = [15 : 30 : 345]) rotate(a) translate([22.5, 0, 2.4]) cylinder(d = 6, h = 20);   // grip flutes
        translate([-sock / 2, -sock / 2, -0.01]) cube([sock, sock, knob_sock]);
        translate([0, 0, 9]) rotate([0, 90, 0]) cylinder(d = m3_tap, h = 30);                  // M3 set screw into plastic
    }
}

module scale_disk() {
    difference() {
        cylinder(d = 140, h = 2, $fn = 180);
        translate([0, 0, -1]) cylinder(d = lid_hole + 2, h = 4);
    }
    for (a = [0 : 1 : 359]) rotate(a) translate([58, -0.25, 2]) cube([a % 10 == 0 ? 8 : (a % 5 == 0 ? 6 : 4), 0.5, 0.6]);
    for (a = [-170 : 10 : 180]) rotate(a) translate([51, 0, 2]) linear_extrude(0.6)
        text(str(a), size = 3.2, font = FONT, halign = "center", valign = "center");
}

module track_seg(i) {
    a = seg[i][0];  b = seg[i][1];
    difference() {
        union() {
            translate([a, -fl_w / 2, z_fl]) cube([b - a, fl_w, fl_t]);
            translate([a, 0, z_ft]) rotate([90, 0, 90]) linear_extrude(b - a) rib_profile();
            for (s = [-1, 1]) translate([a, s * tab_y, z_fl]) linear_extrude(fl_t) tab2d(false);
        }
        if (i < len(seg) - 1) for (s = [-1, 1]) translate([b, s * tab_y, z_fl - 1]) linear_extrude(fl_t + 2) tab2d(true);
        for (d = det) if (d > a && d < b) translate([d, 0, z_rt - 4]) cylinder(d = 3.1, h = 5);          // detents
        for (x = [ceil(a / 10) * 10 : 10 : b - 1])                                                       // mm from the axis
            translate([x - 0.3, 9, z_ft - 0.6]) cube([0.6, x % 50 == 0 ? 11 : 6, 1]);
        for (x = [ceil(a / 50) * 50 : 50 : b - 20]) translate([x + 1.2, 17.5, z_ft - 0.6]) linear_extrude(1)
            text(str(x), size = 3, font = FONT, valign = "center");
        for (d = det) if (d > a && d < b) {
            translate([d - 0.4, -20.5, z_ft - 0.6]) cube([0.8, 11.5, 1]);
            translate([d + 1.5, -16, z_ft - 0.6]) linear_extrude(1) text(str(round(d / inch), " in"), size = 4, font = FONT, valign = "center");
        }
    }
}

module carriage(D = det[0]) {
    difference() {
        union() {
            translate([D - car_front, -car_w / 2, z_ft]) cube([car_front + car_back, car_w, car_top - z_ft]);
            translate([D + bt, -post_w / 2, car_top - 0.01]) cube([post_t, post_w, post_top - car_top]);
            hull() {
                translate([D + bt + post_t - 0.01, -3, car_top]) cube([0.01, 6, 36]);
                translate([D + bt + post_t - 0.01, -3, car_top]) cube([car_back - bt - post_t, 6, 0.01]);
            }
        }
        translate([D - car_front - 1, 0, z_ft - 0.01]) rotate([90, 0, 90]) linear_extrude(car_front + car_back + 2)
            offset(delta = 0.3) rib_profile();
        translate([D, 0, z_ft]) cylinder(d = m3_tap, h = car_top);                                     // lock screw
        for (s = [-1, 1]) translate([D + bt - 0.01, s * det_hole_dy, H - det_led_above_holes]) rotate([0, 90, 0]) {
            cylinder(d = m3, h = post_t + 1);
            translate([0, 0, post_t - nut_t + 0.01]) nut_trap();
        }
        translate([D + bt + 1, -post_w / 2 - 1, H - 6]) cube([0.6, post_w + 2, 0.6]);                 // LED height mark
    }
}

// ---------------------------------------------------------------- assembly view (stand-ins in color)
module assembly(rot = 25, D = det[1]) {
    color("SlateGray") base();
    for (i = [0 : len(seg) - 1]) color("SlateGray") track_seg(i);
    rotate(rot) {
        color("Peru") rotor();
        color("Peru") frame();
        color("ForestGreen") translate([x_bb, -bw / 2, H - bh / 2]) cube([bt, bw, bh]);                  // test board
        color("SteelBlue") translate([x_bb - ats_h, -ats / 2, H - ats / 2]) cube([ats_h, ats, ats]);      // ATS
        color("LightCyan", 0.8) for (y = [-20, 0, 20], z = [-22.68, 0, 22.68])
            translate([x_bf, y, H + z]) rotate([0, 90, 0]) cylinder(d1 = 9, d2 = 20, h = h_exit);           // optics (EST shape)
        color("Coral", 0.25) translate([0, 0, H]) rotate([0, 90, 0]) cylinder(d1 = 20, d2 = 20 + 2 * 120 * tan(7.5), h = 120);
        color("Gainsboro") translate([0, 0, shaft_z0]) shaft();
        color("DimGray") translate([0, 0, knob_z0]) knob();
    }
    color("Peru") translate([0, 0, knob_z0 - 3]) scale_disk();
    color("Peru") carriage(D);
    color("ForestGreen") translate([D, -11, H - 25]) cube([bt, 22, 36]);                                  // detector board
    color("Indigo") translate([D - 1, -1.75, H - 1.4]) cube([1, 3.5, 2.8]);                               // detector LED
}

// ---------------------------------------------------------------- selection (print orientation for parts)
if (part == "assembly") assembly();
if (part == "assembly_0") assembly(rot = 0);
if (part == "base") translate([0, 0, base_t]) base();
if (part == "rotor") rotor();
if (part == "frame") translate([0, 0, -(x_bb - fr_t)]) rotate([0, -90, 0]) frame();
if (part == "shaft") translate([0, 0, shaft_s / 2]) rotate([0, 90, 0]) shaft();
if (part == "knob") knob();
if (part == "scale") scale_disk();
if (part == "track1") translate([-seg[0][0], 0, base_t]) track_seg(0);
if (part == "track2") translate([-seg[1][0], 0, base_t]) track_seg(1);
if (part == "carriage") translate([-det[0], 0, -z_ft]) carriage(det[0]);
