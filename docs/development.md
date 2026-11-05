# Development

Use FreeCAD with its bundled Python and Part modules; system Python cannot build the geometry. The checked desktop version is FreeCAD 1.1.4. The reviewed snapshots are static solids and open directly.

`kuvi_model.py` loads the CSV parameters and provides shared primitives, source import and static document creation. `kuvi_assembly.py` builds the enclosure and mounts. Buttons, USB and detailed hardware live in their own modules. `validate.py` checks saved geometry; `capture.py` produces actual viewport images. `export_model.py` publishes a STEP assembly and eight checked STL files; refresh them after approving model changes.

Edit a named entry in `scripts/parameters.csv` to change a dimension or fitting allowance. Use the CSV Group column to find primary component dimensions, advanced construction offsets or preview spacing. There is no Python defaults table. `kuvi_model.build()` constructs an unsaved document from that file. Review and validate it before explicitly saving over the active revision's `kuvi.FCStd`. The active revision's `model.py` offers `construct()` for the same purpose. Historical helpers only open and inspect their own saved geometry.

For MCP automation, compute `shapes = kuvi_model.geometry(parameters)` in a background geometry job, then call `kuvi_model.create_document(shapes, parameters)` on FreeCAD's GUI thread. Document creation, recompute, saving and camera changes must stay on the GUI thread. Do not recreate the old per-part Python-feature callbacks or run broad Booleans against the imported electronics assembly.

`validate.run(doc)` reads saved parts and returns a report. An explicit output path is required to write a report. For background checks, first copy shapes on the GUI thread and pass the dictionary to `validate.check_shapes(shapes)`. Optional mesh checks use MeshPart. Captures write to `previews/` and restore camera/visibility/transparency without saving those presentation changes.

The three revision READMEs and helpers state their purpose. Original supplier files live in `references/`. Screw geometry is generated from the CSV, without a competing cached-shape source. Default model work stays in the active revision; the shared CSV and latest-preview refresh are required exceptions.
