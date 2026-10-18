# SPDX-License-Identifier: LGPL-2.1-or-later

"""Overlay what the PartDesign feature selected in the tree does to the model.

- Pad, Revolution, additive loft/pipe/primitive: added material (green)
- Pocket, Groove, Hole, subtractive loft/pipe/primitive: removed material (red)
- Patterns, Mirrored and other features without their own add/sub shape:
  the difference to the previous feature, added green and removed red
- Fillet, Chamfer, Draft, Thickness: the edges/faces they act on (orange)
- Sketch: its geometry (yellow)

The overlay is drawn on top of everything (x-ray), is not pickable and never
becomes part of the document. Only whole-object selections (as made in the
tree) trigger it; picking faces or edges in the 3D view does not.
"""

import FreeCAD as App
import FreeCADGui as Gui
import Part
from pivy import coin
from PySide import QtCore

ADD_COLOR = (0.15, 0.85, 0.25)
SUB_COLOR = (0.95, 0.2, 0.15)
DRESSUP_COLOR = (1.0, 0.55, 0.0)
SKETCH_COLOR = (1.0, 0.85, 0.0)
TRANSPARENCY = 0.55
LINE_WIDTH = 4

SUBTRACTIVE = ("PartDesign::Pocket", "PartDesign::Groove", "PartDesign::Hole")
DRESSUP = ("PartDesign::Fillet", "PartDesign::Chamfer", "PartDesign::Draft", "PartDesign::Thickness")

# Volumes below this are boolean noise, not material a feature added/removed.
MIN_VOLUME = 1e-6


def highlights_for(obj):
    """Return a list of body-local (shape, color, filled) to draw for obj."""
    tid = obj.TypeId
    if tid in DRESSUP:
        base, subs = obj.Base
        elements = [base.Shape.getElement(s) for s in subs if s]
        return [(Part.makeCompound(elements), DRESSUP_COLOR, False)] if elements else []
    if tid.startswith("Sketcher::"):
        return [(obj.Shape, SKETCH_COLOR, False)]
    if not obj.isDerivedFrom("PartDesign::Feature"):
        return []

    shape = getattr(obj, "AddSubShape", None)
    if shape is not None and not shape.isNull():
        subtractive = tid in SUBTRACTIVE or tid.startswith("PartDesign::Subtractive")
        return [(shape, SUB_COLOR if subtractive else ADD_COLOR, True)]

    # Patterns, Mirrored, MultiTransform, ... carry no add/sub shape of their
    # own, so compare against the feature they were built on.
    if obj.Shape.isNull():
        return []
    base = obj.BaseFeature
    if base is None or base.Shape.isNull():
        return [(obj.Shape, ADD_COLOR, True)]
    added = obj.Shape.cut(base.Shape)
    removed = base.Shape.cut(obj.Shape)
    return [(s, c, True) for s, c in ((added, ADD_COLOR), (removed, SUB_COLOR)) if s.Volume > MIN_VOLUME]


def parent_matrix(top, subname):
    """Global transform of the container that the selected object lives in.

    subname is the selection path below top, e.g. "Body.Pad." for a Pad in a
    Body selected through a Link or Part. Going through getSubObject picks up
    the placements of every Part, Link and Body along that path.
    """
    path = subname.rstrip(".").split(".")
    if len(path) < 2:
        # Selected object is top itself, its shape already carries its placement.
        if not subname:
            return App.Matrix()
        return top.getSubObject("", 1, App.Matrix())[1]
    return top.getSubObject(".".join(path[:-1]) + ".", 1, App.Matrix())[1]


def make_node(shape, color, filled):
    inp = coin.SoInput()
    inp.setBuffer(shape.writeInventor())
    geometry = coin.SoDB.readAll(inp)
    if geometry is None:
        return None

    pick = coin.SoPickStyle()
    pick.style = coin.SoPickStyle.UNPICKABLE

    style = coin.SoDrawStyle()
    style.lineWidth = LINE_WIDTH
    style.setOverride(True)

    material = coin.SoMaterial()
    material.diffuseColor = color
    material.emissiveColor = tuple(c * 0.5 for c in color)
    material.transparency = TRANSPARENCY if filled else 0.0
    material.setOverride(True)

    # SoAnnotation renders after the rest of the scene without depth test,
    # so the highlight stays visible inside/behind the solid.
    root = coin.SoAnnotation()
    for child in (pick, style, material, geometry):
        root.addChild(child)
    return root


def scenegraphs(doc):
    gdoc = Gui.getDocument(doc.Name)
    try:
        views = gdoc.mdiViewsOfType("Gui::View3DInventor")
    except Exception:
        views = [gdoc.ActiveView]
    return [v.getSceneGraph() for v in views if hasattr(v, "getSceneGraph")]


class Highlighter:
    def __init__(self):
        self.nodes = []  # (scenegraph, node)
        self.pending = False
        self.running = False

    def start(self):
        if not self.running:
            Gui.Selection.addObserver(self)
            self.running = True
            self.schedule()

    def stop(self):
        if self.running:
            Gui.Selection.removeObserver(self)
            self.running = False
        self.clear()

    # Selection observer callbacks. Selection changes often arrive in bursts
    # (clear + add), so redraw once after the burst instead of per callback.
    def addSelection(self, doc, obj, sub, pnt):
        self.schedule()

    def removeSelection(self, doc, obj, sub):
        self.schedule()

    def setSelection(self, doc):
        self.schedule()

    def clearSelection(self, doc):
        self.schedule()

    def schedule(self):
        if not self.pending:
            self.pending = True
            QtCore.QTimer.singleShot(0, self.refresh)

    def clear(self):
        for sg, node in self.nodes:
            if sg.findChild(node) >= 0:
                sg.removeChild(node)
        self.nodes = []

    def refresh(self):
        self.pending = False
        self.clear()
        if not self.running:
            return
        # Unresolved selection: top-level object plus the path to the selected
        # object, so features shown through Links/Parts land in the right place.
        for sel in Gui.Selection.getSelectionEx("", 0):
            top = sel.Object
            for subname in sel.SubElementNames or ("",):
                # A path not ending in "." names a face/edge/vertex picked in
                # the 3D view, not a feature selection.
                if subname and not subname.endswith("."):
                    continue
                self.show(top, subname)

    def show(self, top, subname):
        obj = top.getSubObject(subname, 1) if subname else top
        if obj is None:
            return
        try:
            highlights = highlights_for(obj)
            if not highlights:
                return
            placement = App.Placement(parent_matrix(top, subname))
            graphs = scenegraphs(top.Document)
            for shape, color, filled in highlights:
                shape = shape.copy()
                shape.Placement = placement.multiply(shape.Placement)
                node = make_node(shape, color, filled)
                if node is None:
                    continue
                for sg in graphs:
                    sg.addChild(node)
                    self.nodes.append((sg, node))
        except Exception as e:
            App.Console.PrintWarning("FeatureHighlight: {}: {}\n".format(obj.Label, e))


highlighter = Highlighter()
