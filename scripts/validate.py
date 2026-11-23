"""Validate saved Kuvi solids without rebuilding them or modifying the document."""
import json
from pathlib import Path
from itertools import combinations
import FreeCAD as App
from kuvi_model import ROOT, V, parameters
PRINTED = ['FrontCarrier','RearCasing','BatteryTray','ButtonLeft','ButtonRight','ButtonCapLeft','ButtonCapRight']
COMPONENTS = ['Battery','Speaker','HapticPCB','HapticHeader','HapticMotor','USBMaleHousing','USBMaleHeatShrink','USBFemaleHousing','USBFemalePlate','USBFemaleHeatShrink','USBRibbon']
def overlap(a,b):
    if not a.BoundBox.intersect(b.BoundBox):return 0.
    return a.common(b).Volume

def _native(shapes, p):
    r={'revision':'print-test','solids':{},'collisions':[],'slider_samples':[],'tool_access':{},'wire_route_advisories':[]}
    for n in PRINTED+[n for n in shapes if 'Screw' in n]:
        s=shapes[n];r['solids'][n]={'valid':s.isValid(),'count':len(s.Solids)}
    allowed=[{'ButtonLeft','ButtonCapLeft'},{'ButtonRight','ButtonCapRight'},{'USBMaleHousing','USBMaleHeatShrink'}]
    for a,b in combinations(PRINTED+COMPONENTS,2):
        if {a,b} in allowed:continue
        v=overlap(shapes[a],shapes[b])
        if v>.02:r['collisions'].append([a,b,round(v,4)])
    import FreeCAD as App
    # Plugs disconnected; include underside solder geometry during flat sliding.
    for dy,angle in [(offset,0) for offset in (-50,-40,-30,-20,-15,-10,-5,-2,-1,0)]:
        hits=[]
        moving=[('HapticPCB',shapes['HapticPCB']),('HapticMotor',shapes['HapticMotor']),('UndersideContacts',shapes['HapticHeader'].Solids[-1])]
        for a,original in moving:
            s=original.translated(V(0,dy,0))
            for b in ['RearCasing','Speaker']:
                v=overlap(s,shapes[b])
                if v>.02:hits.append([a,b,round(v,4)])
        r['slider_samples'].append({'dy':dy,'front_up_degrees':-angle,'hits':hits})
    stages={
      'board_before_tray':(['BoardToolEnvelope'+str(i) for i in (1,2,3)],['FrontCarrier']),
      'battery_before_closure':(['BatteryToolEnvelope'+str(i) for i in (1,2,3)],['FrontCarrier','BatteryTray','Battery','BatteryStrap']),
      'haptic_L_key_front_open':(['VibratorToolEnvelope1'],['RearCasing','HapticPCB','HapticMotor','HapticHeader']),
      'closure':(['ClosureToolEnvelope1','ClosureToolEnvelope2'],PRINTED+COMPONENTS),
      'usb':(['USBToolEnvelope1','USBToolEnvelope2'],PRINTED+COMPONENTS)}
    for stage,(tools,obstacles) in stages.items():
        hits=[]
        for a in tools:
            for b in obstacles:
                if b not in shapes: continue
                v=overlap(shapes[a],shapes[b])
                if v>.02:hits.append([a,b,round(v,4)])
        r['tool_access'][stage]=hits
    for a in shapes:
        if 'Wire' not in a:continue
        for b in PRINTED+['Battery','Speaker']:
            if a.startswith('SpeakerWire') and b=='Speaker':continue  # intended lead entry
            if b not in shapes: continue
            v=overlap(shapes[a],shapes[b])
            if v>.02:r['wire_route_advisories'].append([a,b,round(v,4)])
    r['free_ribbon_length_mm']=shapes['USBRibbon'].Volume/p['USBWireWidth']/p['USBWireThickness']
    return r

def run(doc, output=None, mesh=True):
    """Read-only checks; returns a report; writes only when a path is supplied."""
    shapes = {o.Name:o.Shape.copy() for o in doc.Objects if o.isDerivedFrom('Part::Feature')}
    return check_shapes(shapes, output, mesh)


def check_shapes(shapes, output=None, mesh=True):
    missing = (set(PRINTED+COMPONENTS) - shapes.keys())
    if missing: raise ValueError('Not the current Kuvi assembly: '+str(sorted(missing)))
    p = parameters()
    r = _native(shapes, p)
    r['front_insertion'] = []
    for offset in (-15,-10,-5,-3,-1,0):
        hits=[]
        for name in ('FrontCarrier','BatteryTray','Battery','BatteryStrap','BatteryPads'):
            if name not in shapes: continue
            vol=overlap(shapes[name].translated(V(0,offset,0)), shapes['RearCasing'])
            if vol>.02: hits.append([name,vol])
        r['front_insertion'].append({'offset':offset,'hits':hits})
    # Straight insertion toward the rear seat; reverse path provides removal.
    speaker = shapes['Speaker']
    r['speaker_insertion'] = []
    for offset in (-20, -10, -5, -2, -1, 0):
        moved = speaker.translated(V(0, offset, 0))
        vol = overlap(moved, shapes['RearCasing'])
        r['speaker_insertion'].append({'offset': offset, 'overlap_mm3': vol})
    r['buttons']=[]
    for side,sign,ref in [('Left',-1,'SwitchB'),('Right',1,'SwitchA')]:
        axis=V(sign*p['EarAxisX'],0,p['EarAxisZ']);stem=shapes['Button'+side];switch=shapes[ref]
        row={'side':side,'rest_gap':stem.distToShape(switch)[0],
             'gap_after_0_2_press':stem.translated(-axis*p['ButtonRestGap']).distToShape(switch)[0], 'hits':[]}
        for offset in (-p['ButtonTargetStroke'],0,p['ButtonOutwardTestMid'],p['ButtonOutwardFloat']):
            for name in ('Button'+side,'ButtonCap'+side):
                moved=shapes[name].translated(axis*offset)
                for wall in ('FrontCarrier','RearCasing'):
                    vol=overlap(moved,shapes[wall])
                    if vol>.001: row['hits'].append([offset,name,wall,vol])
        r['buttons'].append(row)
    r['nuts']=[]
    for i,x in enumerate((-p['USBFemaleHolePitch']/2,p['USBFemaleHolePitch']/2),1):
        nut=shapes['USBMountNut'+str(i)];spun=nut.copy()
        spun.rotate(V(x,0,p['USBFemaleZ']),V(0,1,0),30)
        r['nuts'].append({'seated_overlap':overlap(nut,shapes['RearCasing']),
                         'rotation_interference':overlap(spun,shapes['RearCasing'])})
    r['meshes']={}
    if mesh:
        import MeshPart
        for name in PRINTED:
            m=MeshPart.meshFromShape(Shape=shapes[name],LinearDeflection=.1,AngularDeflection=.35,Relative=False)
            r['meshes'][name]={'closed':m.isSolid(),'nonmanifold':m.hasNonManifolds()}
    r['checks']={
      'valid_single_solids':all(v['valid'] and v['count']==1 for v in r['solids'].values()),
      'no_part_collisions':not r['collisions'],
      'pcb_insertion':all(not x['hits'] for x in r['slider_samples']),
      'front_insertion':all(not x['hits'] for x in r['front_insertion']),
      'speaker_insertion':all(x['overlap_mm3'] < .001 for x in r['speaker_insertion']),
      'tool_access':all(not x for x in r['tool_access'].values()),
      'button_reach':all(abs(x['rest_gap']-p['ButtonRestGap'])<.01 and x['gap_after_0_2_press']<.01 and not x['hits'] for x in r['buttons']),
      'nut_fit':all(x['seated_overlap']<.001 and x['rotation_interference']>.001 for x in r['nuts']),
      'ribbon_length':abs(r['free_ribbon_length_mm']-p['USBExposedValue'])<.01,
      'closed_print_meshes':all(x['closed'] and not x['nonmanifold'] for x in r['meshes'].values()) if mesh else None}
    r['ok']=all(v for v in r['checks'].values() if v is not None)
    r['scope']='Saved geometry, native booleans, static switch reach and sampled assembly. Flexible wire intersections are routing advisories, not fixed-location fit failures. Physical print fits, switch operation, cable bend limits and strength require testing.'
    if output is not None:
        path=Path(output);path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(r,indent=2))
    return r
