# Assembly and first print

1. Insert the button stems from inside the front carrier. Fit the ear caps from outside while supporting each stem; do not use the onboard switches as a backstop.
2. Secure the Waveshare with its three M2 screws before installing the battery tray.
3. Fit the battery with its pads and strap, then attach the tray at all three mounting points.
4. With the rear casing open and USB extension absent, slide the vibrator PCB in horizontally. Align its front-corner hole and tighten the single internal screw using a 1.5 mm L-shaped Allen key. Leave its other hole unused.
5. Connect the vibrator's sideways-facing plugs. Install the internal USB extension and rear socket with its two nuts and screws. Keep the ribbon in its intended route.
6. Slide the speaker straight into the open rear pocket until it seats against the shoulder. Route its lead through the rounded side notch. There is no keeper, latch or gasket; pull the speaker out along the same path for service. The nominal 0.15 mm per-side fit allowance needs a physical check; use a thin removable shim if the print is loose rather than forcing the speaker into a tight pocket.
7. Connect the front and rear assemblies, seat the straight lip and tighten the two front closure screws. Do not pull a binding joint together with the screws.

## Print parts

Use the ready-made STL files in [exports/printables](../exports/printables/). The seven printed solids are: `FrontCarrier`, `RearCasing`, `BatteryTray`, `ButtonLeft`, `ButtonRight`, `ButtonCapLeft`, `ButtonCapRight`.

Reference electronics, wires, screws and nuts are not print parts. Flexible wire paths are illustrative: route the actual leads during assembly. 

Before printing the enclosure, choose the printer, nozzle, material and layer settings. Print small screw-boss, stem/socket, mating-lip and speaker-pocket coupons. Then check the slicer's supports, wall coverage and mesh warnings for each part. No production G-code is provided.

After assembly, confirm both buttons click and return, the battery stays supported without compression, cables are not pinched, and the speaker/vibrator do not rattle. The current geometry checks do not replace these physical tests.
