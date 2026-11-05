"""Current Kuvi geometry, parameters and safe static-document creation.

Run inside FreeCAD. Model inputs come from scripts/parameters.csv.
Rebuilds are unsaved unless an output is explicitly supplied.
World axes: X left/right, Y front/rear, Z up. Dimensions are millimetres.
"""
from pathlib import Path
import math
import csv
import FreeCAD as App
import Part
ROOT = Path(__file__).resolve().parents[1]
ACTIVE_REVISION = ROOT / 'revisions/03-print-test'
FINAL = ACTIVE_REVISION / 'kuvi.FCStd'
PARAMETERS_FILE = ROOT / 'scripts/parameters.csv'
V = App.Vector

def box(dx,dy,dz,x,y,z):
    return Part.makeBox(dx,dy,dz,V(x,y,z))


def cyl(r,h,x,y,z,axis=(0,1,0)):
    return Part.makeCylinder(r,h,V(x,y,z),V(*axis))


def union(parts):
    result=parts[0]
    for part in parts[1:]:
        result=result.fuse(part)
    return result.removeSplitter()


def rounded_box(dx,dy,dz,x,y,z,r=1.):
    s=box(dx,dy,dz,x,y,z)
    return s.makeFillet(r,s.Edges)


def rounded_rect_y(width,depth,height,x,y,z,radius,rim=0.):
    """Round the four edges parallel to thickness Y; keep the rims crisp."""
    shape=box(width,depth,height,x,y,z)
    edges=[e for e in shape.Edges if e.BoundBox.YLength>depth-.001]
    shape=shape.makeFillet(radius,edges)
    if rim:
        shape=shape.makeFillet(rim,[e for e in shape.Edges if e.BoundBox.YLength<.001])
    return shape


def tube_path(points,r):
    # Solid segment unions with round joints; conceptual routing, no bend spec.
    parts=[]
    for a,b in zip(points,points[1:]):
        va,vb=V(*a),V(*b); direction=vb-va
        parts.append(Part.makeCylinder(r,direction.Length,va,direction))
    parts.extend(Part.makeSphere(r,V(*p)) for p in points[1:-1])
    return union(parts)


def radial_bar(x,z,y,cz,end_radius,width=5.,depth=2.):
    dx,dz=x,z-cz; length=math.hypot(dx,dz)
    a=V(x,y,z); b=V(dx/length*end_radius,y,cz+dz/length*end_radius)
    n=V(-dz/length*width/2,0,dx/length*width/2)
    wire=Part.makePolygon([a+n,b+n,b-n,a-n,a+n])
    return Part.Face(wire).extrude(V(0,depth,0))


def screw(x,y,z,length,diameter=None,axis=(0,-1,0),kind="plastic"):
    from kuvi_fasteners import fastener
    return fastener(x,y,z,length,diameter,axis,kind)


def parameter_rows():
    with PARAMETERS_FILE.open(newline='') as f:
        rows = list(csv.DictReader(f))
    names = [row['Parameter'] for row in rows]
    if len(names) != len(set(names)):
        raise ValueError('Duplicate parameter names in parameters.csv')
    return [(row['Parameter'], float(row['Value']), row['Meaning']) for row in rows]


def parameters():
    p = {name: value for name, value, _ in parameter_rows()}
    if not all(math.isfinite(value) for value in p.values()):
        raise ValueError('Parameter values must be finite numbers')
    return p


def geometry(p=None):
    from kuvi_assembly import geometry as assemble
    return assemble(p if p is not None else parameters())


def open_model(path=None):
    path = Path(path or FINAL).resolve()
    for doc in App.listDocuments().values():
        if doc.FileName and Path(doc.FileName).resolve() == path:
            App.setActiveDocument(doc.Name)
            return doc
    return App.openDocument(str(path))


def reference_shapes(p):
    source = Part.read(str(ROOT / 'references/ESP32-S3-Touch-AMOLED-1/ESP32-S3-Touch-AMOLED-1_75.stp'))
    solids = source.Solids
    selections={
        'PCB':([0],(0.06,.32,.43),'PCB — exact mounting-hole geometry'),
        'DisplayGlass':([664],(.04,.06,.08),'Display cover — verified diameter 48.96 mm'),
        'DisplayStack':([665],(.13,.14,.17),'AMOLED stack'),
        'USB_C':(list(range(250,272)),(.72,.74,.77),'USB-C — downward, original geometry'),
        'ModuleConnectorA':([5],(.92,.89,.78),'MX1.25 connector A — pin assignment to verify'),
        'ModuleConnectorB':([275],(.92,.89,.78),'MX1.25 connector B — pin assignment to verify'),
        'SwitchA':([277],(.6,.61,.65),'Onboard switch A — PWR/BOOT mapping to verify'),
        'SwitchB':([278],(.6,.61,.65),'Onboard switch B — PWR/BOOT mapping to verify'),
        'MicrophoneA':([300],(.7,.64,.41),'Microphone package A — port face to verify'),
        'MicrophoneB':([585],(.7,.64,.41),'Microphone package B — port face to verify'),
        'FactoryM2Inserts':([648,649,650],(.72,.6,.3),'Factory M2 threaded inserts — keep installed'),
        'GPIOHeader':(list(range(652,661)),(.16,.16,.18),'8-pin GPIO / UART header'),
    }
    used = {i for indices, _, _ in selections.values() for i in indices}
    selections['OtherElectronics'] = ([i for i in range(len(solids)) if i not in used], (.32,.34,.37), 'Remaining source electronics')
    result = {}
    for name, (indices, color, label) in selections.items():
        shape = Part.makeCompound([solids[i] for i in indices])
        shape.Placement = App.Placement(V(0,p['WaveshareYOffset'],p['CenterZ']), App.Rotation(V(1,0,1),180))
        result[name] = (shape, color, label)
    return result


def group_color(name):
    if 'Envelope' in name or name in ('AntennaKeepout','MicrophoneDucts'):
        return 'Clearances', (.9,.35,.08)
    if 'Screw' in name or 'Nut' in name:
        return 'Fasteners', (.78,.8,.83)
    if name.startswith('USB') or 'Wire' in name:
        color = (.8,.06,.05) if name.endswith('Red') else (.15,.16,.18)
        return 'Harness', color
    if name.startswith('Battery'):
        return 'BatteryAssembly', ((.72,.74,.77) if name=='Battery' else (.85,.83,.75))
    if name.startswith('Speaker'):
        return 'SpeakerAssembly', ((.15,.16,.17) if name in ('Speaker','SpeakerLeadSleeve') else (.85,.87,.85))
    if name.startswith('Haptic'):
        return 'HapticAssembly', ((.07,.08,.09) if name=='HapticPCB' else (.65,.67,.69))
    if name=='RearCasing' or name.startswith('ButtonCap'):
        return 'Enclosure', (.9,.9,.9)
    return 'Enclosure', (.2,.24,.26)


def create_document(shapes, p=None, refs=None, name='kuvi_rebuilt'):
    """GUI-thread step: create plain solids, without Python feature callbacks."""
    p = p or parameters()
    refs = refs or reference_shapes(p)
    doc = App.newDocument(name)
    groups = {n: doc.addObject('App::DocumentObjectGroup', n) for n in (
        'Enclosure','Waveshare','BatteryAssembly','SpeakerAssembly',
        'HapticAssembly','Fasteners','Harness','Clearances')}
    for objname, (shape, color, label) in refs.items():
        obj = doc.addObject('Part::Feature', objname)
        obj.Shape = shape.copy(); obj.Label = label
        groups['Waveshare'].addObject(obj)
        if App.GuiUp: obj.ViewObject.ShapeColor = color
    for objname, shape in shapes.items():
        obj = doc.addObject('Part::Feature', objname); obj.Shape = shape.copy()
        group, color = group_color(objname); groups[group].addObject(obj)
        if App.GuiUp: obj.ViewObject.ShapeColor = color
        if group=='Clearances': obj.Visibility = False
    doc.addObject('App::DocumentObjectGroup','BuildInfo')
    doc.BuildInfo.addProperty('App::PropertyString','ParametersJSON')
    import json
    doc.BuildInfo.ParametersJSON = json.dumps(p, sort_keys=True)
    doc.Label = 'Kuvi — rebuilt print-test geometry'
    doc.recompute()
    return doc


def build(output=None):
    """Construct an unsaved model; save only when an output is explicitly supplied."""
    p = parameters()
    if output is not None:
        output = Path(output).resolve()
        if output == FINAL.resolve() or output.exists():
            raise FileExistsError('Use FreeCAD Save As explicitly to replace a reviewed snapshot')
    doc = create_document(geometry(p), p)
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        doc.saveAs(str(output))
    return doc
