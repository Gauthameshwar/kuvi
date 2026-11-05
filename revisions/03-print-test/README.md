# Print-test model

The current design uses measured parts, a rear USB-C extension, a three-point battery tray, a recessed speaker with a screwless keeper, and a horizontal slide-in vibrator mount secured by one screw. The white bun-shaped ear caps operate guided button stems. A straight alignment lip locates the casing halves; two front screws clamp them together.

Open `kuvi.FCStd` directly in FreeCAD. `model.py` opens and inspects this snapshot. `model.py.construct()` returns an unsaved model built by the shared geometry modules from `scripts/parameters.csv`, the only dimension table. Save approved changes in this folder without creating another revision.

Ready for a fit-test print. Printer tolerances, clips, button return and physical vibration performance still need testing. See `docs/assembly.md` from the repository root.

Purpose: Active design; construct from scripts/parameters.csv and update this folder in place.
