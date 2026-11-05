# Repository Guidelines

## Philosophy

Kuvi is a physical, serviceable robot, not just a CAD rendering. Prefer simple parts, accessible screws, measured component envelopes and a realistic assembly order. Keep the repository small and readable. Document the current design and meaningful decisions; do not accumulate transcripts, competing reports, recovery scripts or minor version snapshots.

## Revision Scope

Revision folders are named for their purpose: `01-concept`, `02-serviceable`, and `03-print-test`. The active design is `revisions/03-print-test/`. Unless the user requests a new revision, update that revision in place. Do not create a new revision for a minor change.

By default, keep model changes inside the active revision folder. Historical revisions are immutable unless explicitly requested. Each revision contains exactly `kuvi.FCStd`, `model.py`, and a brief `README.md`. Keep temporary files, FreeCAD backups and experiments outside these folders.

The shared parameter CSV and latest previews are required exceptions: update them as necessary for an authorized model change. Changes to other shared scripts, documentation or references require a relevant user request; do not perform unrelated cleanup.

## Dimensions and Geometry

`scripts/parameters.csv` is the sole source of model dimensions, placements, fillets and fitting allowances. It belongs in `scripts/`, never `cad/`. Edit a named CSV entry rather than duplicating a physical dimension in Python. Scripts load it at runtime; do not add a competing defaults table or revision-specific parameter CSV. Mathematical ratios, indices, numerical kernel tolerances and rendering settings may remain in code.

The Python modules explain construction: shared primitives and document creation, enclosure/mounts, buttons, USB routing, and fasteners. Keep those responsibilities distinct. Historical `model.py` helpers inspect embedded snapshot geometry; the active helper also constructs the current model from the shared CSV. Each helper and README must explain its revision's purpose.

Original supplier drawings, photos and sketches belong in `references/`. Distinguish measured dimensions from assumptions. Preserve original reference files.

## Verification and Previews

Use actual FreeCAD tools and saved geometry. Never simulate success. Rebuild and check affected geometry, assembly paths, screw access and clearances before saving. Use plain solids; avoid the old per-part Python callback rebuild and broad Booleans against imported electronics. Document and GUI writes stay on FreeCAD's GUI thread.

`previews/` contains only the latest reviewed model. Refresh it after visual changes. Include front-angled and rear-angled exploded views and a rear-side angled transparent view. Restore all placements, visibility, transparency and camera state after capture; never save an exploded assembly as the CAD model.


Fit checks do not certify printer tolerances, switch operation or physical strength. Keep those limitations brief and specific. Explain what changed and what was verified.
