"""Replace previews with actual views of the current reviewed model only."""
from pathlib import Path
import shutil
import tempfile
import FreeCAD as App
import FreeCADGui as Gui
from kuvi_model import ROOT, FINAL, V, box, parameters

def capture(doc, output=None):
    if not doc.FileName or Path(doc.FileName).resolve()!=FINAL.resolve():
        raise ValueError('Previews must come from the current reviewed revision, not history or a draft')
    output=Path(output or ROOT/'previews');output.mkdir(parents=True,exist_ok=True)
    p=parameters();App.setActiveDocument(doc.Name);view=Gui.activeDocument().activeView()
    features=[o for o in doc.Objects if o.isDerivedFrom('Part::Feature')]
    saved={o.Name:(o.Placement.copy(),o.Visibility,o.ViewObject.Transparency) for o in features}
    camera=view.getCamera();animation=view.isAnimationEnabled();section=None
    clear={o.Name for o in doc.Clearances.Group}
    board={o.Name for o in doc.Waveshare.Group}
    staging=tempfile.TemporaryDirectory(prefix='kuvi-views-');paths=[]
    def reset():
        for o in features:
            o.Placement=saved[o.Name][0];o.Visibility=o.Name not in clear;o.ViewObject.Transparency=0
    def angle(rear=False):
        view.viewAxonometric()
        if rear:view.setCameraOrientation(App.Rotation(V(0,0,1),180).multiply(view.getCameraOrientation()).Q)
    def shot(name):
        view.fitAll();path=Path(staging.name)/(name+'.png')
        view.saveImage(str(path),1200,1000,'Current');paths.append(path)
    try:
        view.setAnimationEnabled(False);reset()
        view.viewFront();shot('front');view.viewRear();shot('rear');angle();shot('assembled')
        doc.RearCasing.ViewObject.Transparency=80;angle(True);shot('transparent-rear')
        reset()
        for o in features:
            name=o.Name;dy=0;dz=0
            if 'Wire' in name:o.Visibility=False;continue
            if name in board or name.startswith('BoardScrew'):dy=-p['PreviewBoardOffset']
            elif name in ('FrontCarrier','ButtonLeft','ButtonRight','ButtonCapLeft','ButtonCapRight') or name.startswith('ClosureScrew'):dy=-p['PreviewFrontOffset']
            elif name.startswith('Battery'):dy=-p['PreviewBatteryOffset']
            elif name.startswith('Speaker'):dy=p['PreviewSpeakerOffset']
            elif name.startswith('Haptic'):dy=p['PreviewRearOffset'];dz=p['PreviewHapticLift']
            elif name=='RearCasing' or name.startswith('USB'):dy=p['PreviewRearOffset']
            placement=o.Placement.copy();placement.Base=placement.Base+V(0,dy,dz);o.Placement=placement
        angle();shot('exploded-front');angle(True);shot('exploded-rear')
        reset()
        for o in features:o.Visibility=o.Name=='RearCasing'
        view.viewFront();shot('speaker-pocket')
        for o in features:o.Visibility=False
        section=doc.addObject('Part::Feature','CaptureFloorSection')
        section.Shape=doc.RearCasing.Shape.common(box(100,100,15,-50,-20,0));section.ViewObject.ShapeColor=(.9,.9,.9)
        for name in ('HapticPCB','HapticMotor','HapticHeader','HapticScrew1'):doc.getObject(name).Visibility=True
        angle();shot('vibrator-mount')
        # Publish a complete new set only after all images have rendered.
        for old in output.iterdir():
            if old.is_file() and old.suffix.lower() in ('.png','.jpg','.jpeg','.webp'):old.unlink()
        for path in paths:shutil.copy2(path,output/path.name)
    finally:
        if section:doc.removeObject(section.Name)
        for name,(placement,visible,transparency) in saved.items():
            obj=doc.getObject(name);obj.Placement=placement;obj.Visibility=visible;obj.ViewObject.Transparency=transparency
        view.setCamera(camera);view.setAnimationEnabled(animation);staging.cleanup()
    return [str(output/path.name) for path in paths]
