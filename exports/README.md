# Kuvi exports

These files come from the current `03-print-test` model. No FreeCAD installation or Python scripts are needed to use them.

- **kuvi.step** — the assembled robot, including separate enclosure parts, reference electronics, cables and fasteners. Construction clearances and tool envelopes are excluded. Import into a STEP-capable CAD application to edit the solid geometry. FreeCAD parameters and feature history are not transferred; support varies by application.
- **printables/** — eight individual STL files for the parts to print. Screws, electronics and other purchased components are excluded. STL is a mesh format; use STEP for CAD editing.
- **verification.json** — STEP round-trip and printable mesh checks.

All dimensions are in **millimetres**. STL does not encode units, so select millimetres in your slicer. Each STL is translated to the origin without rotation. Choose a suitable print orientation, supports and material in your slicer; these files are for the first physical fit test, not a validated production print profile. See [assembly notes](../docs/assembly.md).

To refresh these files after approving changes, open the saved current model in FreeCAD and run:

```python
import sys
sys.path.insert(0, '/absolute/path/to/kuvi/scripts')
import export_model
export_model.export()
```
