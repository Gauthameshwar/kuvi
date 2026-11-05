"""Construct detailed screws from the shared CSV; unspecified thread profiles are estimates."""
import math
import FreeCAD as App
import Part
V = App.Vector
_cache = {}

def fastener(x, y, z, length, diameter, axis, kind='plastic'):
    from kuvi_model import parameters
    p = parameters()
    diameter = diameter if diameter is not None else p['ScrewDiameter']
    prefix = {'plastic':'Plastic', 'board':'Board', 'usb':'USB'}[kind]
    head_d, head_h = p[prefix+'HeadDiameter'], p[prefix+'HeadHeight']
    machine = kind != 'plastic'
    pitch = p['MachineThreadPitch' if machine else 'PlasticThreadPitch']
    root = p['MachineRootRadius' if machine else 'PlasticRootRadius']
    tip = 0 if machine else p['PlasticTipLength']
    key = (kind,length,diameter,head_d,head_h,pitch,root,tip,
           p['PlasticHexAcrossFlats'],p['PlasticSocketDepth'],
           p['MachineDriveWidth'],p['MachineDriveLength'],p['MachineDriveDepth'])
    if key not in _cache:
        cap = Part.makeCylinder(head_d/2,head_h,V(0,0,-head_h))
        if machine:
            w,l,h=p['MachineDriveWidth'],p['MachineDriveLength'],p['MachineDriveDepth']
            drive=Part.makeBox(w,l,h,V(-w/2,-l/2,-head_h)).fuse(Part.makeBox(l,w,h,V(-l/2,-w/2,-head_h)))
        else:
            radius=p['PlasticHexAcrossFlats']/math.sqrt(3)
            pts=[V(radius*math.cos(i*math.pi/3),radius*math.sin(i*math.pi/3),-head_h) for i in range(6)]
            drive=Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(V(0,0,p['PlasticSocketDepth']))
        cap=cap.cut(drive)
        shaft=Part.makeCylinder(root,length-tip)
        if tip:shaft=shaft.fuse(Part.makeCone(root,0,tip,V(0,0,length-tip)))
        helix=Part.makeHelix(pitch,length-tip-pitch,root)
        pts=[V(root-p['ThreadRootOverlap'],0,0),V(diameter/2,0,pitch*.22),V(root-p['ThreadRootOverlap'],0,pitch*.44)]
        profile=Part.Wire(Part.makePolygon(pts+[pts[0]]).Edges)
        ridge=Part.Wire(helix.Edges).makePipeShell([profile],True,True)
        ridge.translate(V(0,0,pitch*.25))
        shape=cap.fuse(shaft).fuse(ridge).removeSplitter()
        if not shape.isValid() or len(shape.Solids)!=1:raise ValueError('Invalid screw geometry')
        _cache[key]=shape
    shape=_cache[key].copy()
    shape.Placement=App.Placement(V(x,y,z),App.Rotation(V(0,0,1),V(*axis)))
    return shape
