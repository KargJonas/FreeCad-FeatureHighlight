# SPDX-License-Identifier: LGPL-2.1-or-later

"""FreeCAD startup hook: registers the toggle command and its toolbar.

This addon defines no workbench. FreeCAD imports freecad/<Addon>/init_gui.py
for every installed addon, which is what makes that possible.
"""

import os

import FreeCADGui as Gui

from . import commands
from .highlighter import highlighter

# This file is at <addon-root>/freecad/FeatureHighlight/init_gui.py.
_ADDON_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_ICONS_DIR = os.path.join(_ADDON_ROOT, "Resources", "Icons")

_TARGET_WORKBENCH = "PartDesignWorkbench"
_TOOLBAR = "Feature Highlight"


def active_workbench_name():
    """Internal name of the workbench being set up.

    FreeCADGui.activeWorkbench().name() raises during a core workbench's first
    activation, so look the handler up by identity instead.
    """
    active = Gui.activeWorkbench()
    for name, handler in Gui.listWorkbenches().items():
        if handler is active:
            return name
    return ""


class Manipulator:
    """Adds the toggle as a one-button toolbar to the PartDesign workbench."""

    def modifyToolBars(self):
        if active_workbench_name() != _TARGET_WORKBENCH:
            return []
        return [
            {"append": _TOOLBAR, "toolBar": ""},
            {"append": "FeatureHighlight_Toggle", "toolBar": _TOOLBAR},
        ]


Gui.addIconPath(_ICONS_DIR)
Gui.addWorkbenchManipulator(Manipulator())

if commands.enabled():
    highlighter.start()
