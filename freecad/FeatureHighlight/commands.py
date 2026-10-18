# SPDX-License-Identifier: LGPL-2.1-or-later

"""The FeatureHighlight_Toggle command, which turns the highlighting on and off."""

import FreeCAD as App
import FreeCADGui as Gui

from .highlighter import highlighter

PREFS = App.ParamGet("User parameter:BaseApp/Preferences/Mod/FeatureHighlight")


def enabled():
    return PREFS.GetBool("Enabled", True)


class ToggleCommand:
    def GetResources(self):
        return {
            "MenuText": "Feature highlight",
            "ToolTip": (
                "Highlight what the PartDesign feature selected in the tree adds (green) "
                "or removes (red), without making it visible or editing it"
            ),
            "Pixmap": "FeatureHighlight.svg",
            "Accel": "V, H",
            "Checkable": enabled(),
        }

    def IsActive(self):
        return True

    def Activated(self, checked):
        PREFS.SetBool("Enabled", bool(checked))
        if checked:
            highlighter.start()
        else:
            highlighter.stop()


Gui.addCommand("FeatureHighlight_Toggle", ToggleCommand())
