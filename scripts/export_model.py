"""Publish the reviewed assembly as STEP and its eight printed parts as STL."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import FreeCAD as App
import Import
import Mesh
import MeshPart
import Part

from kuvi_model import FINAL, ROOT, open_model
from validate import PRINTED


def export(doc=None):
    """Export current saved geometry; leave the document and camera unchanged."""
    doc = doc or open_model()
    if not doc.FileName or Path(doc.FileName).resolve() != FINAL.resolve():
        raise ValueError('Export the reviewed 03-print-test model only.')
    objects = [o for o in doc.Objects if o.isDerivedFrom('Part::Feature')
               and not any(g.Name == 'Clearances' for g in o.InList)]
    output = ROOT / 'exports'
    output.mkdir(exist_ok=True)
    with TemporaryDirectory(prefix='kuvi-export-') as temp:
        stage = Path(temp)
        step = stage / 'kuvi.step'
        Import.export(objects, str(step))
        roundtrip = Part.read(str(step))
        expected = Part.makeCompound([o.Shape for o in objects])
        if not roundtrip.isValid() or len(roundtrip.Solids) != len(expected.Solids):
            raise ValueError('STEP round-trip lost or invalidated solids.')
        volume_difference = abs(roundtrip.Volume - expected.Volume)
        relative_volume_difference = volume_difference / expected.Volume
        before = expected.optimalBoundingBox(False, False)
        after = roundtrip.optimalBoundingBox(False, False)
        bounds_difference = max(abs(getattr(before, a + b) - getattr(after, a + b))
                                for a in 'XYZ' for b in ('Min', 'Max'))
        # STEP surface conversion can alter numerical volume integration slightly.
        if relative_volume_difference > 0.0005 or bounds_difference > 0.01:
            raise ValueError('STEP round-trip exceeded geometry tolerances.')
        results = {}
        for name in PRINTED:
            obj = doc.getObject(name)
            if obj is None or not obj.Shape.isValid() or len(obj.Shape.Solids) != 1:
                raise ValueError('Invalid printable part: ' + name)
            shape = obj.Shape.copy()
            box = shape.BoundBox
            shape.translate(App.Vector(-box.XMin, -box.YMin, -box.ZMin))
            # Export quality settings, not model dimensions. AngularDeflection is radians.
            mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=0.05,
                                          AngularDeflection=0.15, Relative=False)
            path = stage / (name + '.stl')
            mesh.write(str(path))
            loaded = Mesh.Mesh(str(path))
            if not loaded.isSolid() or loaded.hasNonManifolds():
                raise ValueError('STL is not a closed manifold: ' + name)
            results[name] = {'triangles': loaded.CountFacets, 'closed': True}
        # Publish only after every export has passed its round-trip check.
        printed = output / 'printables'
        printed.mkdir(exist_ok=True)
        step.replace(output / step.name)
        for name in PRINTED:
            (stage / (name + '.stl')).replace(printed / (name + '.stl'))
        for stale in printed.glob('*.stl'):
            if stale.stem not in PRINTED:
                stale.unlink()
        report = {'source': str(FINAL.relative_to(ROOT)), 'units': 'mm',
                  'step': {'file': 'kuvi.step', 'objects': len(objects),
                           'solids': len(roundtrip.Solids), 'valid': True,
                           'relative_volume_difference': relative_volume_difference,
                           'max_bounds_difference_mm': bounds_difference},
                  'printables': results}
        (output / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    return report
