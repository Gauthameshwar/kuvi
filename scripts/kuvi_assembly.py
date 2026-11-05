"""Two-piece Kuvi enclosure, designed in the order it can be assembled.

No imported-electronics Booleans are performed here. All shapes are native Part
primitives. The full Waveshare STEP remains in kuvi_model's reference groups.
"""
import math
import FreeCAD as App
import Part
from kuvi_model import V, box, cyl, union, rounded_box, rounded_rect_y, radial_bar, screw, tube_path
_cache = {}

def body_volume(p, inset=0):
    """Round upper head plus a generously rounded, smoothly blended lower plinth."""
    r = p['HeadRadius'] - inset
    cy = p['HeadCenterY']
    cz = p['CenterZ']
    sphere = Part.makeSphere(r, V(0, cy, cz))
    base = rounded_box(p['AssemblyBaseWidth'] - 2 * inset, p['AssemblyBaseDepth'] - 2 * inset, p['AssemblyBaseHeight'] - 2 * inset, -p['AssemblyBaseX'] + inset, p['AssemblyBaseY'] + inset, inset, p['AssemblyBaseFillet'] - inset)
    merged = sphere.fuse(base).removeSplitter()
    seams = []
    for edge in merged.Edges:
        try:
            if type(edge.Curve).__name__ == 'BSplineCurve':
                seams.append(edge)
        except TypeError:
            pass
    merged = merged.makeFillet(p['AssemblyMergedRadius'], seams)
    return merged.common(box(p['AssemblyWidth'], p['AssemblyDepth'], p['AssemblyHeight'], -p['AssemblyX2'], -p['AssemblyY3'], inset)).removeSplitter()

def tool(x, y, z, axis, p):
    direction = V(*axis)
    origin = V(x, y, z)
    shaft = Part.makeCylinder(4 / 2, p['DriverShaftReach'], origin, direction)
    handle = Part.makeCylinder(p['DriverHandleDiameter'] / 2, p['AssemblyHandleLength'], origin + direction * p['DriverShaftReach'], direction)
    return shaft.fuse(handle)

def geometry(p):
    key = tuple(sorted(p.items()))
    if key in _cache:
        return _cache[key]
    r, cy, cz = (p['HeadRadius'], p['HeadCenterY'], p['CenterZ'])
    t, fs, gap = (p['Wall'], p['FrontSplit'], p['SeamGap'])
    outer = body_volume(p)
    inner = body_volume(p, t)
    clip = box(p['AssemblyClipWidth'], p['AssemblyClipDepth'], p['AssemblyClipHeight'], -p['AssemblyClipX'], -p['AssemblyClipY'], 0)
    skin = outer.cut(inner).common(clip)
    front = skin.common(box(p['AssemblyFrontWidth'], fs + p['AssemblyFrontDepth'], p['AssemblyFrontHeight'], -p['AssemblyFrontX'], -p['AssemblyFrontY'], 0))
    rear = skin.common(box(p['AssemblyRearWidth'], p['AssemblyRearDepth'], p['AssemblyRearHeight'], -p['AssemblyRearX'], fs + gap, 0))
    aperture = cyl(p['GlassRadius'] + p['GlassClearance'], p['AssemblyApertureLength'], 0, -p['AssemblyApertureY'], cz)
    liner = cyl(p['GlassRadius'] + p['GlassClearance'] + p['AssemblyLinerRadius'], p['AssemblyLinerLength'], 0, -p['AssemblyLinerY'], cz).cut(aperture)
    fascia = outer.common(box(p['AssemblyFasciaWidth'], p['AssemblyFasciaDepth'], p['AssemblyFasciaHeight'], -p['AssemblyFasciaX'], -p['AssemblyFasciaY'], 0))
    front = union([front, liner, fascia]).cut(aperture)
    mounts = [(p['AssemblyMountsValue'], cz + p['AssemblyMountsValue2']), (-p['AssemblyMountsValue3'], cz), (p['AssemblyMountsValue'], cz - p['AssemblyMountsValue2'])]
    board_screws = []
    envelopes = {}
    for i, (x, z) in enumerate(mounts, 1):
        polar = math.hypot(x, z - cz)
        px, pz = (x / polar * 27, cz + (z - cz) / polar * 27)
        stem = cyl(p['AssemblyStemRadius'], p['AssemblyStemLength'], px, p['AssemblyStemY'], pz)
        lug = cyl(p['AssemblyLugRadius2'], p['AssemblyLugLength2'], x, p['AssemblyLugY'], z).fuse(radial_bar(x, z, p['AssemblyLugY'], cz, p['AssemblyLugEndRadius'], depth=p['AssemblyLugDepth']))
        lug = lug.cut(cyl(p['AssemblyLugRadius'], p['AssemblyLugLength'], x, p['AssemblyLugY2'], z))
        front = union([front, stem, lug])
        board_screws.append(screw(x, p['AssemblyY'], z, p['AssemblyLength'], p['AssemblyDiameter'], kind='board'))
        envelopes['BoardToolEnvelope' + str(i)] = tool(x, p['AssemblyEnvelopesBoardtoolenvelopeStrIValue'], z, (0, 1, 0), p)
    entry_radius = math.sqrt((r - t) ** 2 - (fs + gap - cy) ** 2) - p['LipClearance']
    lip_outer = cyl(entry_radius, p['AssemblyLipOuterLength'], 0, -p['AssemblyLipOuterY'], cz)
    lip_inner = cyl(entry_radius - p['AssemblyLipInnerRadius'], p['AssemblyLipInnerLength'], 0, -p['AssemblyLipInnerY'], cz)
    lip = lip_outer.cut(lip_inner).common(box(p['AssemblyLipWidth'], p['LipDepth'] + p['AssemblyLipDepth'], p['AssemblyLipHeight'], -p['AssemblyLipX'], fs - p['AssemblyLipY'], 0))
    lip = lip.cut(box(p['AssemblyLipWidth'], p['AssemblyLipDepth2'], p['AssemblyLipHeight2'], -p['AssemblyLipX'], fs - p['AssemblyLipY2'], 0))
    land = outer.cut(lip_inner).common(box(p['AssemblyLandWidth'], p['AssemblyLandDepth'], p['AssemblyLandHeight'], -p['AssemblyLandX'], fs - p['AssemblyLandY'], 0))
    land = land.cut(box(p['AssemblyLandWidth'], p['AssemblyLandDepth2'], p['AssemblyLandHeight2'], -p['AssemblyLandX'], fs - p['AssemblyLandY2'], 0))
    front = union([front, lip, land])
    closure_screws = []
    for i, angle in enumerate((180 - p['ClosureAngleDegrees'], p['ClosureAngleDegrees']), 1):
        x = p['ClosureRadius'] * math.cos(math.radians(angle))
        z = cz + p['ClosureRadius'] * math.sin(math.radians(angle))
        front = front.fuse(cyl(p['AssemblyFrontRadius'], fs - p['AssemblyFrontLength'], x, p['AssemblyFrontY2'], z))
        front = front.cut(cyl(p['AssemblyFrontRadius5'], fs + p['AssemblyFrontLength5'], x, -p['AssemblyFrontY5'], z)).cut(cyl(p['AssemblyFrontRadius2'], p['AssemblyFrontLength2'], x, -p['AssemblyFrontY3'], z))
        boss = union([cyl(p['AssemblyBossRadius4'], p['AssemblyBossLength3'], x, fs + gap, z), radial_bar(x, z, fs + gap, cz, r + p['AssemblyBossEndRadius'], p['AssemblyBossWidth'], p['AssemblyBossDepth'])]).common(outer)
        boss = boss.cut(cyl(p['PilotDiameter'] / 2, p['AssemblyBossLength'], x, fs + gap, z))
        rear = rear.fuse(boss)
        clearance = union([cyl(p['AssemblyClearanceRadius'], p['LipDepth'] + p['AssemblyClearanceLength'], x, fs, z), radial_bar(x, z, fs, cz, r + p['AssemblyClearanceEndRadius'], p['AssemblyClearanceWidth'], p['LipDepth'] + p['AssemblyClearanceDepth'])])
        front = front.cut(clearance)
        closure_screws.append(screw(x, p['AssemblyY2'], z, p['ClosureScrewLength'], axis=(0, p['AssemblyAxis'], 0)))
        envelopes['ClosureToolEnvelope' + str(i)] = tool(x, -p['AssemblyEnvelopesClosuretoolenvelopeStrIValue'], z, (0, -1, 0), p)
    bl, bh, bt, bc, by, bz = [p[n] for n in ('BatteryLength', 'BatteryHeight', 'BatteryThickness', 'BatteryClearance', 'BatteryY', 'BatteryZ')]
    cw, ch = (bl + 2 * bc, bh + 2 * bc)
    depth = bt + p['BatteryRetainerGap'] + 2
    tray = rounded_rect_y(cw + p['AssemblyTrayWidth'], depth, ch + p['AssemblyTrayHeight'], -cw / 2 - p['AssemblyTrayX'], by - p['AssemblyTrayY'], bz - bc - p['AssemblyTrayZ'], p['AssemblyTrayCornerRadius'], p['AssemblyTrayRimRadius'])
    cavity = box(cw, depth + p['AssemblyCavityDepth'], ch, -cw / 2, by, bz - bc)
    tray = tray.cut(cavity)
    tray = tray.cut(box(p['AssemblyTrayWidth2'], p['AssemblyTrayDepth'], p['AssemblyTrayHeight2'], -bl / 2 - p['AssemblyTrayX2'], by - p['AssemblyTrayY2'], bz + bh - p['AssemblyTrayZ']))
    battery_screws = []
    for i, sign in enumerate((-1, 1), 1):
        x = sign * p['BatteryMountX']
        front = front.fuse(cyl(p['AssemblyFrontRadius3'], by - p['AssemblyFrontLength3'] - p['AssemblyFrontLength'], x, p['AssemblyFrontY2'], cz))
        front = front.cut(cyl(p['PilotDiameter'] / 2, p['AssemblyFrontLength4'], x, by - p['AssemblyFrontY4'], cz))
        wing = rounded_rect_y(abs(x) - cw / 2 + p['AssemblyWingWidth2'], p['AssemblyWingDepth'], p['AssemblyWingHeight'], x - p['AssemblyWingX'] if sign < 0 else cw / 2, by - p['AssemblyWingY'], cz - p['AssemblyWingZ'], p['AssemblyWingCornerRadius'], p['AssemblyWingRimRadius'])
        boss = cyl(p['AssemblyBossRadius2'], p['AssemblyBossLength2'], x, by - p['AssemblyBossY'], cz)
        boss = boss.makeFillet(p['AssemblyBossRadius3'], [e for e in boss.Edges if type(e.Curve).__name__ == 'Circle'])
        tray = union([tray, wing, boss]).cut(cyl(p['AssemblyTrayRadius'], p['AssemblyTrayLength'], x, by - p['AssemblyTrayY3'], cz))
        battery_screws.append(screw(x, by, cz, p['BatteryMountScrewLength']))
        envelopes['BatteryToolEnvelope' + str(i)] = tool(x, by + p['AssemblyEnvelopesBatterytoolenvelopeStrIValue'], cz, (0, 1, 0), p)
    top_z = p['BatteryTopMountZ']
    if top_z - 3 <= bz + bh + 1:
        raise ValueError('Upper battery mount needs clearance above the wrapped cell')
    crown = cyl(p['AssemblyCrownRadius'], by - p['AssemblyCrownLength'] - p['AssemblyCrownLength2'], 0, p['AssemblyCrownY'], top_z).common(outer)
    root = crown.common(box(p['AssemblyRootWidth'], fs - p['AssemblyRootDepth'], p['AssemblyRootHeight'], -p['AssemblyRootX'], p['AssemblyRootY'], 0))
    post = union([root, crown.common(lip_outer)]).cut(box(p['AssemblyPostWidth'], p['AssemblyPostDepth'], p['AssemblyPostHeight'], -p['AssemblyPostX'], p['AssemblyPostY'], cz + p['AssemblyPostZ']))
    front = front.fuse(post).cut(cyl(p['PilotDiameter'] / 2, p['AssemblyFrontLength4'], 0, by - p['AssemblyFrontY4'], top_z))
    base_z = bz + bh + p['AssemblyBaseZValue']
    outline = Part.makePolygon([V(-p['AssemblyOutlineX'], by - p['AssemblyOutlineY'], base_z), V(p['AssemblyOutlineX'], by - p['AssemblyOutlineY'], base_z), V(p['AssemblyOutlineX2'], by - p['AssemblyOutlineY'], top_z), V(-p['AssemblyOutlineX2'], by - p['AssemblyOutlineY'], top_z), V(-p['AssemblyOutlineX'], by - p['AssemblyOutlineY'], base_z)])
    tab = Part.Face(outline).extrude(V(0, p['AssemblyTabY'], 0))
    tab = tab.makeFillet(p['AssemblyTabRadius'], [e for e in tab.Edges if e.BoundBox.YLength > p['AssemblyTabValue']])
    tab = tab.makeFillet(p['AssemblyTabRadius2'], [e for e in tab.Edges if e.BoundBox.YLength < p['AssemblyTabValue2']])
    boss = cyl(p['AssemblyBossRadius2'], p['AssemblyBossLength2'], 0, by - p['AssemblyBossY'], top_z)
    boss = boss.makeFillet(p['AssemblyBossRadius3'], [e for e in boss.Edges if type(e.Curve).__name__ == 'Circle'])
    tab = union([tab, boss]).common(lip_outer)
    tray = union([tray, tab]).cut(cyl(p['AssemblyTrayRadius'], p['AssemblyTrayLength'], 0, by - p['AssemblyTrayY3'], top_z))
    battery_screws.append(screw(0, by, top_z, p['BatteryMountScrewLength']))
    envelopes['BatteryToolEnvelope3'] = tool(0, by + p['AssemblyEnvelopesBatterytoolenvelopeValue'], top_z, (0, 1, 0), p)
    strap_z = cz + p['BatteryStrapSlotZOffset']
    half = cw / 2 + p['BatteryStrapOuterMargin']
    for sign in (-1, 1):
        tray = tray.cut(box(p['AssemblyTrayWidth3'], depth + p['AssemblyTrayDepth2'], p['AssemblyTrayHeight3'], half - p['AssemblyTrayX3'] if sign > 0 else -half - p['AssemblyTrayX4'], by - p['AssemblyTrayY3'], strap_z))
    battery = rounded_box(bl, bt, bh, -bl / 2, by, bz, p['AssemblyBatteryFillet'])
    band = -bl / 2 + p['BatteryTapeLength']
    battery = battery.common(box(p['BatteryTapeLength'] + p['AssemblyBatteryWidth'], bt + p['AssemblyBatteryDepth'], bh + p['AssemblyBatteryHeight'], -bl / 2 - p['AssemblyBatteryX2'], by - p['AssemblyBatteryY'], bz - p['AssemblyBatteryZ'])).fuse(battery.common(box(bl, bt + p['AssemblyBatteryDepth'], bh + p['AssemblyBatteryHeight'], band, by - p['AssemblyBatteryY'], bz - p['AssemblyBatteryZ'])))
    horizontal = bool(round(p['SpeakerHorizontal']))
    sw, sl = (p['SpeakerLength'], p['SpeakerWidth']) if horizontal else (p['SpeakerWidth'], p['SpeakerLength'])
    st = p['SpeakerThickness']
    sr = p['SpeakerRecess']
    sc, cr = (p['SpeakerClearance'], p['SpeakerCornerRadius'])
    sy, sz = (p['SpeakerY'], p['SpeakerZ'])
    sd = p['SpeakerCavityDepth']
    pcw, pch = (sw + 2 * sc, sl + 2 * sc)

    def profile(w, d, h, y, rad):
        return rounded_rect_y(w, d, h, -w / 2, y, sz - h / 2, rad)
    cup = profile(pcw + p['AssemblyCupWidth'], p['AssemblyCupDepth'], pch + p['AssemblyCupHeight'], sy, cr + sc + p['AssemblyCupRadius']).cut(profile(pcw, p['AssemblyCupDepth2'], pch, sy - p['AssemblyCupY'], cr + sc)).common(outer)
    seat = profile(pcw + p['AssemblySeatWidth'], p['AssemblySeatDepth'], pch + p['AssemblySeatHeight'], sy + sd, cr + sc + p['AssemblySeatRadius']).cut(profile(sw - p['AssemblySeatWidth2'], p['AssemblySeatDepth2'], sl - p['AssemblySeatHeight2'], sy + sd - p['AssemblySeatY'], cr - p['AssemblySeatRadius2'])).common(outer)
    rear = union([rear, cup, seat])
    keeper = profile(pcw + p['AssemblyKeeperWidth2'], p['AssemblyKeeperDepth2'], pch + p['AssemblyKeeperHeight2'], sy - p['AssemblyKeeperY2'], cr + sc + p['AssemblyKeeperRadius2']).cut(profile(sw - p['AssemblyKeeperWidth'], p['AssemblyKeeperDepth'], sl - p['AssemblyKeeperHeight'], sy - p['AssemblyKeeperY'], cr - p['AssemblyKeeperRadius']))
    contact = profile(sw - p['AssemblyContactWidth2'], sr, sl - p['AssemblyContactHeight2'], sy, cr - p['AssemblyContactRadius2']).cut(profile(sw - p['AssemblyContactWidth'], sr + p['AssemblyContactDepth'], sl - p['AssemblyContactHeight'], sy - p['AssemblyContactY'], cr - p['AssemblyContactRadius']))
    keeper = keeper.fuse(contact).removeSplitter()
    clip_t = p['SpeakerClipThickness']
    clip_gap = p['SpeakerClipClearance']
    for sign in (-1, 1):
        armz = sz + sl / 2 + p['AssemblyArmzValue']
        hookz = armz + clip_t
        hook_h = clip_gap + p['SpeakerClipHook']
        arm_z = armz if sign > 0 else 2 * sz - armz - clip_t
        hook_z = hookz if sign > 0 else 2 * sz - hookz - hook_h
        arm = box(p['AssemblyArmWidth'], p['AssemblyArmDepth'], clip_t, -p['AssemblyArmX'], sy - p['AssemblyArmY'], arm_z)
        base = armz + clip_t if sign > 0 else 2 * sz - armz - clip_t
        peak = base + sign * hook_h
        wire = Part.makePolygon([V(-p['AssemblyWireX'], sy + p['AssemblyWireY'], base), V(-p['AssemblyWireX'], sy + p['AssemblyWireY'], peak), V(-p['AssemblyWireX'], sy + p['AssemblyWireY2'], base), V(-p['AssemblyWireX'], sy + p['AssemblyWireY'], base)])
        hook = Part.Face(wire).extrude(V(p['AssemblyHookX'], 0, 0))
        keeper = union([keeper, arm, hook])
        slot_z = armz - clip_gap if sign > 0 else 2 * sz - (armz + clip_t + clip_gap)
        rear = rear.cut(box(p['AssemblyRearWidth2'] + 2 * clip_gap, p['AssemblyRearDepth2'], clip_t + 2 * clip_gap, -p['AssemblyRearX2'] - clip_gap, sy - p['AssemblyRearY'], slot_z))
        recess_z = slot_z if sign > 0 else slot_z - hook_h
        rear = rear.cut(box(p['AssemblyRearWidth2'] + 2 * clip_gap, p['AssemblyRearDepth3'], clip_t + 2 * clip_gap + hook_h, -p['AssemblyRearX2'] - clip_gap, sy + p['AssemblyRearY2'], recess_z))
    relief = box(p['AssemblyReliefWidth'], p['AssemblyReliefDepth'], p['AssemblyReliefHeight'], -sw / 2 - p['AssemblyReliefX2'], sy - p['AssemblyReliefY'], sz - p['AssemblyReliefZ'])
    rear = rear.cut(relief)
    keeper = keeper.cut(relief)
    speaker = rounded_rect_y(sw, st, sl, -sw / 2, sy + sr, sz - sl / 2, cr, p['SpeakerRimRadius'])
    pitch = p['GrillePitch']
    hole_centres = []
    for column in range(-3, 4):
        heights = (-2, -1, 0, 1, 2) if column == 0 else (-p['AssemblyHeightsValue'], p['AssemblyHeightsValue']) if abs(column) == 1 else (-p['AssemblyHeightsValue2'], 0, p['AssemblyHeightsValue2'])
        hole_centres.extend(((column * pitch, h * pitch) for h in heights))
    for x, z in hole_centres:
        surface = V(x, cy + math.sqrt(r * r - x * x - (sz + z - cz) ** p['AssemblySurfaceY']), sz + z)
        normal = surface - V(0, cy, cz)
        normal.normalize()
        hole = Part.makeCylinder(p['GrilleDiameter'] / 2, p['AssemblyHoleLength'], surface - normal * p['AssemblyHoleBase'], normal)
        rear = rear.cut(hole)
    rims = []
    for edge in rear.Edges:
        centre = edge.CenterOfMass
        if 7 < edge.Length < 8 and abs(centre.x) < 12.5 and (abs(centre.z - sz) < 8.5) and ((centre - V(0, cy, cz)).Length > r - 0.2) and (centre.y > sy + sd + 1):
            rims.append(edge)
    if len(rims) != 21:
        raise ValueError('Expected 21 outer grille rims; found ' + str(len(rims)))
    rear = rear.makeFillet(p['GrilleRimRadius'], rims)
    hx, hd = (p['HapticPCBLength'], p['HapticPCBWidth'])
    hy = p['HapticY']
    hz = p['HapticZ']
    pcb_t = p['HapticPCBThickness']
    yf = hy - hd / 2
    yb = hy + hd / 2
    hole_x = -hx / 2 + p['HapticHoleEdgeOffset']
    bed = box(p['AssemblyBedWidth'], hd + p['AssemblyBedDepth'], hz, -p['AssemblyBedX'], yf, 0)
    solder_clearance = box(p['AssemblySolderClearanceWidth'], hy + p['AssemblySolderClearanceDepth'] - yf, p['AssemblySolderClearanceHeight'], -hx / 2 - p['AssemblySolderClearanceX2'], yf - p['AssemblySolderClearanceY'], hz - p['AssemblySolderClearanceZ'])
    bed = bed.cut(solder_clearance)
    lower_lip = box(p['AssemblyLowerLipWidth'], hd + p['AssemblyLowerLipDepth'], p['AssemblyLowerLipHeight'], -p['AssemblyLowerLipX'], yf, hz - p['AssemblyLowerLipZ']).cut(solder_clearance)
    rails = [box(p['AssemblyRailsWidth'], hd + p['AssemblyRailsDepth'], pcb_t + p['AssemblyRailsHeight'], p['AssemblyRailsX'], yf, hz), box(p['AssemblyRailsWidth2'], hd + p['AssemblyRailsDepth'], p['AssemblyRailsHeight2'], p['AssemblyRailsX2'], yf, hz + pcb_t + p['AssemblyRailsZ']), box(p['AssemblyRailsWidth3'], p['AssemblyRailsDepth'], pcb_t + p['AssemblyRailsHeight3'], -p['AssemblyRailsX3'], yb + p['AssemblyRailsY'], hz)]
    rear = union([rear, bed.common(outer), lower_lip.common(outer)] + [q.common(outer) for q in rails])
    anti_rattle = box(p['AssemblyAntiRattleWidth'], p['AssemblyAntiRattleDepth'], p['AssemblyAntiRattleHeight'], p['AssemblyAntiRattleX'], yb - p['AssemblyAntiRattleY'], hz + pcb_t)
    haptic_screws = []
    y = hy - p['HapticHolePitch'] / 2
    rear = rear.cut(cyl(p['PilotDiameter'] / 2, p['AssemblyRearLength'], hole_x, y, hz - p['AssemblyRearZ'], (0, 0, 1)))
    haptic_screws.append(screw(hole_x, y, hz + pcb_t, p['AssemblyLength2'], axis=(0, 0, -p['AssemblyAxis'])))
    envelopes['VibratorToolEnvelope1'] = union([cyl(p['AssemblyEnvelopesVibratortoolenvelopeRadius'], p['AssemblyEnvelopesVibratortoolenvelopeLength'], hole_x, y, hz + pcb_t + p['AssemblyEnvelopesVibratortoolenvelopeZ'], (0, 0, 1)), cyl(p['AssemblyEnvelopesVibratortoolenvelopeRadius'], p['AssemblyEnvelopesVibratortoolenvelopeLength2'], hole_x, y, hz + pcb_t + p['AssemblyEnvelopesVibratortoolenvelopeZ2'], (0, -1, 0))])
    haptic = box(hx, hd, pcb_t, -hx / 2, yf, hz)
    for y in (hy - p['HapticHolePitch'] / 2, hy + p['HapticHolePitch'] / 2):
        haptic = haptic.cut(cyl(p['AssemblyHapticRadius'], pcb_t + p['AssemblyHapticLength'], hole_x, y, hz - p['AssemblyHapticZ'], (0, 0, 1)))
    motor = cyl(p['AssemblyMotorRadius'], p['AssemblyMotorLength'], p['AssemblyMotorX'], hy, hz + pcb_t, (0, 0, 1))
    header = Part.makeCompound([box(p['AssemblyHeaderWidth'], p['AssemblyHeaderDepth'], p['AssemblyHeaderHeight'], -hx / 2 - p['AssemblyHeaderX2'], hy - p['AssemblyHeaderY'], hz + pcb_t), box(p['AssemblyHeaderWidth2'], p['AssemblyHeaderDepth2'], p['AssemblyHeaderHeight2'], -hx / 2, hy - p['AssemblyHeaderY2'], hz - p['AssemblyHeaderZ'])])
    driver = box(p['AssemblyDriverWidth'], p['AssemblyDriverDepth'], p['AssemblyDriverHeight'], -p['AssemblyDriverX'], hy + p['AssemblyDriverY'], hz + pcb_t)
    red = tube_path([(p['AssemblyRedPoints'], hy + p['AssemblyRedPoints2'], hz + pcb_t + p['AssemblyRedPoints3']), (p['AssemblyRedPoints4'], hy + p['AssemblyRedPoints5'], hz + pcb_t + p['AssemblyRedPoints3']), (-p['AssemblyRedPoints6'], hy + p['AssemblyRedPoints6'], hz + pcb_t + p['AssemblyRedPoints7'])], p['AssemblyRedRadius'])
    blue = tube_path([(p['AssemblyBluePoints'], hy + p['AssemblyBluePoints2'], hz + pcb_t + p['AssemblyBluePoints3']), (p['AssemblyBluePoints4'], hy + p['AssemblyBluePoints5'], hz + pcb_t + p['AssemblyBluePoints3']), (-p['AssemblyBluePoints6'], hy + p['AssemblyBluePoints7'], hz + pcb_t + p['AssemblyBluePoints8'])], p['AssemblyBlueRadius'])
    pin_length = 5
    from kuvi_buttons import mechanism
    buttons = []
    button_caps = []
    for sign in (-1, 1):
        guide, stem, cap, pocket, info = mechanism(sign, p)
        guide = guide.common(cyl(entry_radius - p['AssemblyGuideRadius'], p['AssemblyGuideLength'], 0, -p['AssemblyGuideY'], cz))
        front = front.fuse(guide).cut(pocket)
        rear = rear.cut(guide).cut(pocket)
        buttons.append(stem)
        button_caps.append(cap)
    microphones = []
    for sign in (-1, 1):
        microphones.append(tube_path([(sign * p['AssemblyPoints'], p['AssemblyPoints2'], cz - p['AssemblyPoints3']), (sign * p['AssemblyPoints'], p['AssemblyPoints4'], cz - p['AssemblyPoints3']), (sign * p['AssemblyPoints5'], p['AssemblyPoints4'], cz - p['AssemblyPoints6'])], p['AssemblyRadius']))
    mic = Part.makeCompound(microphones)
    front = front.cut(mic)
    rear = rear.cut(mic)
    from kuvi_usb import extension
    front, rear, usb_parts = extension(p, front, rear, outer)
    rear = rear.cut(keeper).removeSplitter()
    wires = {}
    for off, color in ((-0.65, 'Black'), (0.65, 'Red')):
        bp = [(p['BatteryWireBend1X'], p['AssemblyBpValue'], cz - p['AssemblyBpValue2']), (p['BatteryWireBend2X'], p['BatteryWireBend2Y'], cz - p['AssemblyBpValue2']), (p['BatteryWireBend3X'], p['BatteryWireBend3Y'], bz + bh - 2), (p['BatteryWireBend4X'], p['BatteryWireBend4Y'], bz + bh - 1), (-bl / 2 - p['AssemblyBpValue3'], by + bt / 2, bz + bh + p['AssemblyBpValue4'])]
        wires['BatteryWire' + color] = tube_path([(x, y + off, z + off) for x, y, z in bp], 1 / 2)
        # Flexible leads are illustrative; never carve their route into the tray.
        sp = [(p['SpeakerWireBend1X'], p['AssemblySpValue'], cz + p['AssemblySpValue2']), (-p['AssemblySpValue3'], p['SpeakerWireBend2Y'], cz + 8), (p['SpeakerWireBend3X'], p['SpeakerWireBend3Y'], cz + 7), (p['SpeakerWireBend4X'], p['SpeakerWireBend4Y'], cz + 1), (p['SpeakerWireBend5X'], p['AssemblySpValue4'], sz), (-p['AssemblySpValue5'], p['AssemblySpValue6'], sz), (-sw / 2 - p['AssemblySpValue7'], sy + sr + st / 2, sz)]
        wires['SpeakerWire' + color] = tube_path([(x, y + off, z + off) for x, y, z in sp], 1 / 2)
    for i, off in enumerate((-2.54, 0, 2.54), 1):
        wires['HapticWire' + str(i)] = tube_path([(p['AssemblyWiresHapticwireStrIPoints'], p['AssemblyWiresHapticwireStrIPoints2'], cz + off), (-p['AssemblyWiresHapticwireStrIPoints3'], p['AssemblyWiresHapticwireStrIPoints4'], p['AssemblyWiresHapticwireStrIPoints5']), (-p['AssemblyWiresHapticwireStrIPoints6'], p['AssemblyWiresHapticwireStrIPoints6'], p['AssemblyWiresHapticwireStrIPoints7']), (-p['AssemblyWiresHapticwireStrIPoints8'], hy + off, hz + pcb_t + p['AssemblyWiresHapticwireStrIPoints9'])], p['AssemblyWiresHapticwireStrIRadius'])
    sleeve = cyl(p['AssemblySleeveRadius'], p['AssemblySleeveLength'], -sw / 2 - p['AssemblySleeveX'], sy + sr + st / 2, sz, (1, 0, 0))
    sleeve = sleeve.makeFillet(p['AssemblySleeveRadius2'], [e for e in sleeve.Edges if type(e.Curve).__name__ == 'Circle'])
    result = {'FrontCarrier': front, 'RearCasing': rear, 'BatteryTray': tray, 'Battery': battery, 'SpeakerLeadSleeve': sleeve, 'Speaker': speaker, 'SpeakerKeeper': keeper, 'HapticAntiRattlePads': anti_rattle, 'HapticPCB': haptic, 'HapticMotor': motor, 'HapticHeader': header, 'HapticDriver': driver, 'HapticMotorLeadRed': red, 'HapticMotorLeadBlue': blue, 'ButtonLeft': buttons[0], 'ButtonRight': buttons[1], 'ButtonCapLeft': button_caps[0], 'ButtonCapRight': button_caps[1], 'MicrophoneDucts': mic, 'AntennaKeepout': box(p['AssemblyResultWidth'], p['AssemblyResultDepth'], p['AssemblyResultHeight'], -p['AssemblyResultX'], p['AssemblyResultY'], cz + p['AssemblyResultZ'])}
    for prefix, items in [('BoardScrew', board_screws), ('BatteryMountScrew', battery_screws), ('ClosureScrew', closure_screws), ('HapticScrew', haptic_screws)]:
        result.update({prefix + str(i): s for i, s in enumerate(items, 1)})
    result.update(wires)
    result.update(envelopes)
    result.update(usb_parts)
    _cache.clear()
    _cache[key] = result
    return result
