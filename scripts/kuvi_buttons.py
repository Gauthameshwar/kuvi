"""Construct the scooped ear caps, stems and stepped guides from CSV inputs."""
import math
import FreeCAD as App
import Part
from kuvi_model import V, box, union

def mechanism(sign, p):
    cz = p['CenterZ']
    r = p['HeadRadius']
    cy = p['HeadCenterY']
    axis = V(sign * p['EarAxisX'], 0, p['EarAxisZ'])
    tip = V(sign * p['EarAxisX'] * p['ButtonActuatorOriginRadius'], p['ButtonActuatorY'], cz + p['EarAxisZ'] * p['ButtonActuatorOriginRadius'])
    rel = tip - V(0, cy, cz)
    along = rel.dot(axis)
    distance = -along + math.sqrt(along * along + r * r - rel.dot(rel))

    def c(rad, length, z):
        return Part.makeCylinder(rad, length, V(0, 0, z))
    guide = c(p['EarGuideRadius2'], distance - p['EarGuideLength2'], p['EarGuideZ']).fuse(c(p['EarGuideRadius'], p['EarGuideLength'], p['EarGuideZ']))
    bore = c(p['EarBoreRadius'], distance + p['EarBoreLength'], p['EarBoreZ'])
    flange_z = p['ButtonFlangeZ']
    flange_pocket = c(p['EarFlangePocketRadius'], p['EarFlangePocketLength'], p['EarFlangePocketZ'])
    guide = guide.cut(bore).cut(flange_pocket)
    # Solid backing toward the front wall; no cavity below the guide sleeve.
    support = box(2 * p['ButtonSupportHalfWidth'], p['ButtonSupportFrontReach'],
                  distance - p['EarGuideLength2'], -p['ButtonSupportHalfWidth'],
                  -p['ButtonSupportFrontReach'], p['EarGuideZ'])
    tip_z = -p['ButtonLeftTipExtension'] if sign < 0 else -p['ButtonRightTipExtension']
    stem = union([c(p['ButtonStemRadius'], distance + p['EarStemLength'] - tip_z, tip_z), c(p['ButtonFlangeRadius'], p['ButtonFlangeThickness'], flange_z)])

    def ellipsoid(rx, ry, rz, centre):
        m = App.Matrix()
        m.A11 = rx
        m.A22 = ry
        m.A33 = rz
        sh = Part.makeSphere(p['EarShRadius']).transformGeometry(m)
        sh.translate(V(*centre))
        return sh
    bun = ellipsoid(p['EarWidthRadius'], p['EarDepthRadius'], p['EarHeight'], (0, 0, 0))
    cap = bun.common(box(p['EarCapWidth'], p['EarCapDepth'], p['EarCapHeight'], -p['EarCapX'], -p['EarCapY'], 0))
    scoop = ellipsoid(p['EarScoopRadiusX'], p['EarScoopRadiusY'], p['EarScoopRadiusZ'], (0, -p['EarScoopCentre'], p['EarScoopCentre2']))
    cap = cap.cut(scoop).cut(c(p['EarSocketRadius'], p['EarSocketDepth'], -p['EarCapZ']))
    cap = cap.cut(Part.makeCone(p['EarEntryRadius'], p['EarSocketRadius'], p['EarEntryDepth'], V(0, 0, -p['EarCapZ'])))
    cap.translate(V(0, 0, distance + p['EarBaseStandOff']))
    m = App.Matrix()
    m.A11 = p['EarRecessRadiusX']
    m.A22 = p['EarRecessRadiusY']
    m.A33 = 1
    opening = c(p['EarOpeningRadius'], p['EarOpeningLength'], 0).transformGeometry(m)
    opening.translate(V(0, 0, distance - p['EarRecessFloorInset']))
    pocket = bore.fuse(flange_pocket).fuse(opening)
    place = App.Placement(tip, App.Rotation(V(0, 0, p['EarPlaceZ']), axis))
    for s in (guide, stem, cap, pocket, support):
        s.Placement = place.multiply(s.Placement)
    return guide, stem, cap, pocket, {
        'radial_running_clearance': p['EarBoreRadius']-p['ButtonStemRadius'],
        'cap_diametral_clearance': 2*(p['EarSocketRadius']-p['ButtonStemRadius']),
        'rest_cap_gap': p['EarBaseStandOff'], 'travel':p['ButtonTargetStroke'],
        'tip_local_z':tip_z, 'support':support}
