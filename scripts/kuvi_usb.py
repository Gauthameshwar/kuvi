"""Construct the internal USB ribbon, connector bodies and rear socket mount from CSV inputs."""
import math
import Part
from kuvi_model import V, box, cyl, rounded_rect_y, rounded_box, screw, union

def ribbon(p):
    r = p['USBBendRadius']
    w = p['USBWireWidth']
    t = p['USBWireThickness']
    if abs(p['USBFemaleZ'] - (p['USBZValue'] + 4 * r)) > 1e-06:
        raise ValueError('Re-route the ribbon when changing socket height or bend radius')
    start = p['USBStartValue']
    end = p['USBFemaleY'] - p['USBFemaleDepth']
    b = p['USBBValue']
    exposed = p['USBExposedValue']
    a = b + (exposed - (end - start) - 2 * math.pi * r) / 2
    z = p['USBZValue']
    if a <= b or end <= b:
        raise ValueError('Cable length cannot fit this routing topology')

    def pt(y, h):
        return V(-w / 2, y, h)

    def ln(y1, z1, y2, z2):
        return Part.makeLine(pt(y1, z1), pt(y2, z2))

    def arc(y1, z1, ym, zm, y2, z2):
        return Part.Arc(pt(y1, z1), pt(ym, zm), pt(y2, z2)).toShape()
    h = t / 2
    edges = [ln(start, z - h, a, z - h), arc(a, z - h, a + r + h, z + r, a, z + 2 * r + h), ln(a, z + 2 * r + h, b, z + 2 * r + h), arc(b, z + 2 * r + h, b - r + h, z + 3 * r, b, z + 4 * r - h), ln(b, z + 4 * r - h, end, z + 4 * r - h), ln(end, z + 4 * r - h, end, z + 4 * r + h), ln(end, z + 4 * r + h, b, z + 4 * r + h), arc(b, z + 4 * r + h, b - r - h, z + 3 * r, b, z + 2 * r - h), ln(b, z + 2 * r - h, a, z + 2 * r - h), arc(a, z + 2 * r - h, a + r - h, z + r, a, z + h), ln(a, z + h, start, z + h), ln(start, z + h, start, z - h)]
    exposed_shape = Part.Face(Part.Wire(edges)).extrude(V(w, 0, 0))
    embedded = 0.0
    return exposed_shape

def extension(p, front, rear, outer):
    fy, fz = (p['USBFemaleY'], p['USBFemaleZ'])
    depth = p['USBFemaleDepth']
    male = rounded_box(p['USBMaleWidth'], p['USBMaleDepth'], p['USBMaleHeight'], -p['USBMaleX'], p['USBMaleY'], p['USBMaleZ'], p['USBMaleFillet'])
    blade = rounded_rect_y(p['USBBladeWidth'], p['USBBladeDepth'], p['USBBladeHeight'], -p['USBBladeX'], p['USBBladeY'], p['USBBladeZ'], p['USBBladeCornerRadius'])
    plate = box(p['USBFemaleWidth'], p['USBPlateDepth'], p['USBFemaleHeight'], -p['USBFemaleWidth'] / 2, fy - p['USBPlateY'], fz - p['USBFemaleHeight'] / 2)
    body = rounded_rect_y(p['USBBodyWidth'], depth - p['USBBodyDepth'], p['USBBodyHeight'], -p['USBBodyX'], fy - depth + p['USBBodyY'], fz - p['USBBodyZ'], p['USBBodyCornerRadius'])
    mouth = rounded_rect_y(p['USBMouthWidth'], p['USBMouthDepth'], p['USBMouthHeight'], -p['USBMouthX'], fy - p['USBMouthY'], fz - p['USBMouthZ'], p['USBMouthCornerRadius'])
    lining = rounded_rect_y(p['USBLiningWidth'], p['USBLiningDepth'], p['USBLiningHeight'], -p['USBLiningX'], fy - p['USBLiningY'], fz - p['USBLiningZ'], p['USBLiningCornerRadius']).cut(mouth)
    plate = plate.cut(mouth)
    body = body.cut(mouth)
    land = rounded_rect_y(p['USBLandWidth'], p['USBLandDepth'], p['USBLandHeight'], -p['USBLandX'], fy - p['USBLandY'], fz - p['USBLandZ'], p['USBLandCornerRadius'])
    rear = rear.fuse(land)
    channel = rounded_rect_y(p['USBChannelWidth'], depth + p['USBChannelDepth'], p['USBChannelHeight'], -p['USBChannelX'], fy - depth - p['USBChannelY'], fz - p['USBChannelZ'], p['USBChannelCornerRadius'])
    recess = rounded_rect_y(p['USBRecessWidth'], p['USBRecessDepth'], p['USBRecessHeight'], -p['USBRecessX'], fy - p['USBRecessY'], fz - p['USBRecessZ'], p['USBRecessCornerRadius'])
    rear = rear.cut(channel).cut(recess)
    parts = {'USBMaleHousing': male, 'USBMaleBlade': blade, 'USBFemaleHousing': body, 'USBFemalePlate': plate, 'USBFemaleLining': lining, 'USBRibbon': ribbon(p), 'USBMaleHeatShrink': box(p['USBPartsWidth'], p['USBPartsDepth'], p['USBPartsHeight'], -p['USBPartsX'], p['USBPartsY'], p['USBPartsZ']), 'USBFemaleHeatShrink': box(p['USBPartsWidth'], p['USBPartsDepth'], p['USBPartsHeight'], -p['USBPartsX'], fy - depth, fz - p['USBPartsZ2'])}
    for i, x in enumerate((-p['USBFemaleHolePitch'] / 2, p['USBFemaleHolePitch'] / 2), 1):
        bore = cyl(p['USBFemaleHoleDiameter'] / 2, p['USBBoreLength'], x, fy - p['USBBoreY'], fz)
        plate = plate.cut(bore)
        rear = rear.cut(bore)
        points = [V(x + p['USBPointsX'] * math.cos(k * math.pi / 3), fy - p['USBPointsY'], fz + p['USBPointsZ'] * math.sin(k * math.pi / 3)) for k in range(6)]
        nut = Part.Face(Part.makePolygon(points + [points[0]])).extrude(V(0, p['USBNutY2'], 0)).cut(cyl(p['USBNutRadius'], p['USBNutLength'], x, fy - p['USBNutY'], fz))
        pocket_points = [V(x + p['USBPocketPointsX'] / math.sqrt(p['USBPocketPointsX2']) * math.cos(k * math.pi / 3), fy - p['USBPocketPointsY'], fz + p['USBPocketPointsZ'] / math.sqrt(p['USBPocketPointsZ2']) * math.sin(k * math.pi / 3)) for k in range(6)]
        pocket = Part.Face(Part.makePolygon(pocket_points + [pocket_points[0]])).extrude(V(0, p['USBPocketY'], 0))
        rear = rear.cut(pocket)
        parts['USBMountScrew' + str(i)] = screw(x, fy, fz, p['USBPartsUsbmountscrewStrILength'], axis=(0, -p['USBPartsUsbmountscrewStrIAxis'], 0), kind='usb')
        parts['USBMountNut' + str(i)] = nut
        from kuvi_assembly import tool
        parts['USBToolEnvelope' + str(i)] = tool(x, fy + p['USBPartsUsbtoolenvelopeStrIValue'], fz, (0, 1, 0), p)
    parts['USBFemalePlate'] = plate
    rear = rear.removeSplitter()
    return (front, rear, parts)
