"""Current measured enclosure prepared for physical fit testing. Open/inspect saved geometry inside FreeCAD."""
from pathlib import Path
import FreeCAD as App

PURPOSE = 'Current measured enclosure prepared for physical fit testing'
MODEL = Path(__file__).resolve().with_name('kuvi.FCStd')

def open_model():
    for doc in App.listDocuments().values():
        if doc.FileName and Path(doc.FileName).resolve() == MODEL:
            App.setActiveDocument(doc.Name)
            return doc
    return App.openDocument(str(MODEL))

def inspect():
    doc = open_model()
    return {o.Name: {'valid': o.Shape.isValid(), 'solids': len(o.Shape.Solids)}
            for o in doc.Objects if o.isDerivedFrom('Part::Feature')}

def construct():
    """Construct this design from scripts/parameters.csv; return an unsaved document."""
    import sys
    sys.path.insert(0, str(MODEL.parents[2] / 'scripts'))
    import kuvi_model
    return kuvi_model.build()

if __name__ == '__main__':
    open_model()
