"""Initial three-piece enclosure concept with provisional component fits. Open/inspect saved geometry inside FreeCAD."""
from pathlib import Path
import FreeCAD as App

PURPOSE = 'Initial three-piece enclosure concept with provisional component fits'
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

if __name__ == '__main__':
    open_model()
