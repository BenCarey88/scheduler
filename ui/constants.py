"""Ui constants."""

from collections import OrderedDict

from PyQt5 import QtGui

from scheduler.api.tree.task import TaskStatus

# General
TASK_STATUS_CHECK_STATES = OrderedDict([
    (TaskStatus.UNSTARTED, 0),
    (TaskStatus.IN_PROGRESS, 1),
    (TaskStatus.COMPLETE, 2)
])

# Colors
BASE_TEXT_COLOR = QtGui.QColor(0, 0, 0)
INACTIVE_TEXT_COLOR = QtGui.QColor(150, 150, 150)
TASK_STATUS_COLORS = {
    TaskStatus.UNSTARTED: BASE_TEXT_COLOR,
    TaskStatus.IN_PROGRESS: QtGui.QColor(175, 100, 255),
    TaskStatus.COMPLETE: QtGui.QColor(100, 160, 36),
}
