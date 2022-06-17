"""Ui constants."""

from collections import OrderedDict

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.tree.task import TaskStatus


# General
TASK_STATUS_CHECK_STATES = OrderedDict([
    (TaskStatus.UNSTARTED, 0),
    (TaskStatus.IN_PROGRESS, 1),
    (TaskStatus.COMPLETE, 2)
])
SHORT_TIMER_INTERVAL = 30000  # every 30s
LONG_TIMER_INTERVAL = 300000 # every 5 mins

# Mime Data
OUTLINER_TREE_MIME_DATA_FORMAT = "outliner_tree_mime_data"
TASK_TAB_TREE_MIME_DATA_FORMAT = "task_tab_tree_mime_data"
ITEM_DIALOG_TREE_MIME_DATA_FORMAT = "item_dialog_tree_mime_data"
PLANNED_ITEM_MIME_DATA_FORMAT = "planned_item_mime_data"

# Colors
BASE_TEXT_COLOR = QtGui.QColor(0, 0, 0)
INACTIVE_TEXT_COLOR = QtGui.QColor(150, 150, 150)
TASK_STATUS_COLORS = {
    TaskStatus.UNSTARTED: BASE_TEXT_COLOR,
    TaskStatus.IN_PROGRESS: QtGui.QColor(175, 100, 255),
    TaskStatus.COMPLETE: QtGui.QColor(100, 160, 36),
}

# Buttons
YES_BUTTON = QtWidgets.QMessageBox.StandardButton.Yes
NO_BUTTON = QtWidgets.QMessageBox.StandardButton.No
CANCEL_BUTTON = QtWidgets.QMessageBox.StandardButton.Cancel
