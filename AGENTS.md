# Repository Guidelines

## Philosophy

Kuvi is a physical, serviceable robot. Prefer simple parts, accessible screws, realistic assembly order and clearly identified provisional measurements. Keep documentation brief and preserve original supplier references.

## Revision Scope

The current snapshot is `revisions/01-concept/`: the initial three-piece head and provisional component layout. Revision names describe their purpose. Unless explicitly requested, make model changes in this revision only and do not create minor version snapshots. Keep earlier revisions unchanged.

Each revision contains exactly `kuvi.FCStd`, `model.py`, and a brief `README.md`. Keep temporary files and FreeCAD backups elsewhere. The historical helper opens and inspects embedded solids; it does not reconstruct the design.

## Verification

Open the CAD file directly in FreeCAD or run its `model.py` helper with FreeCAD Python. Inspect actual geometry and assembly access. Never simulate tool success. These provisional models are historical design studies, not verified print files. Do not infer printer tolerances or physical strength from CAD alone.

## References and Contributions

Preserve original drawings and photos in `references/`. Separate measured dimensions from estimates. Explain the purpose and verification of changes; use short, imperative commit subjects. Shared-file changes need a relevant user request.
