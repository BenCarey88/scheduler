"""Colour constants."""

from PyQt5 import QtGui

from scheduler.api.enums import ItemImportance, ItemStatus

# TODO: start using this module for colors instead of constants


# Base Colors
WHITE = QtGui.QColor(255,255,255)
LIGHT_GREY = QtGui.QColor(235, 235, 235)
DARK_GREY = QtGui.QColor(160, 160, 160)
DARKER_GREY = QtGui.QColor(150, 150, 150)
DARKEST_GREY = QtGui.QColor(110, 110, 110)
BLACK = QtGui.QColor(0, 0, 0)

DARK_RED = QtGui.QColor(227, 36, 43)
RED = QtGui.QColor(250, 60, 10)
# ORANGE = QtGui.QColor(255, 140, 0)
# YELLOW = QtGui.QColor(255, 255, 153)
GREEN = QtGui.QColor(52, 200, 51)
DARK_GREEN = QtGui.QColor(100, 160, 36)
TURQUOISE = QtGui.QColor(0, 255, 204)
# BLUE = QtGui.QColor(0, 0, 200)
PURPLE = QtGui.QColor(175, 100, 255)
# PINK = QtGui.QColor(255,105,180)


# Usage
TASK_STATUS_COLORS = {
    ItemStatus.UNSTARTED: BLACK,
    ItemStatus.IN_PROGRESS: PURPLE,
    ItemStatus.COMPLETE: DARK_GREEN,
}
INACTIVE_TEXT_COLOR = DARKER_GREY
