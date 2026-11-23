# Kuvi

Kuvi is a small desktop robot built around the Waveshare ESP32-S3-Touch-AMOLED-1.75. This repository contains its FreeCAD head enclosure and the source used to build it. Revision names describe their purpose; changes stay in the active print-test revision unless another scope is requested.

**Open [the current model](revisions/03-print-test/kuvi.FCStd) in FreeCAD.** It contains separate parts for printing, reference electronics and hardware. The saved model uses independent solids; opening it does not require running a script.

The enclosure is ready for a fit-test print. Printer/material settings and physical fits have not yet been verified.

## Ready-to-use files

- [STEP assembly](exports/kuvi.step): separate solid parts for editing in other CAD tools.
- [Printable STL parts](exports/printables/): seven parts, in millimetres.
- [Export instructions](exports/README.md): format details and print preparation.

## Where to start

- [Assembly and print testing](docs/assembly.md)
- [Measured components and fit allowances](docs/components.md)
- [Parts pictures and drawings](references/README.md)
- [Design history](docs/history.md): three snapshots, each with one CAD file, one Python helper and one README
- [Geometry checks](docs/validation.json)

## Development

Run `scripts/kuvi.FCMacro` in FreeCAD to open the current model. For source changes, use FreeCAD's Python console:

```python
import sys
sys.path.insert(0, '/absolute/path/to/kuvi/scripts')
import kuvi_model, validate, capture

doc = kuvi_model.open_model()
report = validate.run(doc)
images = capture.capture(doc)
# Edit scripts/parameters.csv, then construct an unsaved model for review:
# rebuilt = kuvi_model.build()
```

Validation checks saved geometry without rebuilding or altering it, and returns a report without writing files unless an output is explicitly supplied. Rebuilds are unsaved unless an output is explicitly supplied. Capture replaces `previews/` with views of the latest reviewed model, including front/rear exploded angles and a transparent rear angle, then restores the user's display settings. See [development notes](docs/development.md).

`scripts/parameters.csv` is the source of truth for dimensions, positions and fit allowances. Geometry scripts read it at runtime.

`scripts/` contains five geometry modules, one opening macro, one validator, one capture tool and one exporter. `references/` holds original supplier files, part photos and sketches. Detailed screw geometry is generated from the CSV as well. `firmware/src/` is reserved for future firmware.

[AGENTS.md](AGENTS.md) defines revision scope, parameter ownership and verification rules.
