"""Ui constants."""

from collections import OrderedDict

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.tree import TaskImportance, TaskStatus


# General
TASK_STATUS_CHECK_STATES = OrderedDict([
    (TaskStatus.UNSTARTED, 0),
    (TaskStatus.IN_PROGRESS, 1),
    (TaskStatus.COMPLETE, 2)
])
TINY_TIMER_INTERVAL = 200    # every 0.2s
SHORT_TIMER_INTERVAL = 30000 # every 30s
LONG_TIMER_INTERVAL = 300000 # every 5m

# Mime Data
OUTLINER_TREE_MIME_DATA_FORMAT = "outliner_tree_mime_data"
TASK_TAB_TREE_MIME_DATA_FORMAT = "task_tab_tree_mime_data"
ITEM_DIALOG_TREE_MIME_DATA_FORMAT = "item_dialog_tree_mime_data"
PLANNED_ITEM_MIME_DATA_FORMAT = "planned_item_mime_data"

# Colors
BLACK = QtGui.QColor(0, 0, 0)
WHITE = QtGui.QColor(255, 255, 255)
BASE_TEXT_COLOR = BLACK
INACTIVE_TEXT_COLOR = QtGui.QColor(150, 150, 150)
TASK_STATUS_COLORS = {
    TaskStatus.UNSTARTED: BASE_TEXT_COLOR,
    TaskStatus.IN_PROGRESS: QtGui.QColor(175, 100, 255),
    TaskStatus.COMPLETE: QtGui.QColor(100, 160, 36),
}
TASK_IMPORTANCE_COLORS = {
    TaskImportance.MINOR: QtGui.QColor(100, 160, 36),
    TaskImportance.MODERATE: QtGui.QColor(234, 121, 0),
    TaskImportance.MAJOR: QtGui.QColor(255, 38, 0),
    TaskImportance.CRITICAL: QtGui.QColor(155, 23, 0),
}
BASE_SCHEDULED_EVENT_COLOR = QtGui.QColor(173, 216, 230)
BASE_SCHEDULED_TASK_COLOR = QtGui.QColor(245, 245, 190)
SCHEDULER_SELECTION_RECT_COLOR = QtGui.QColor(0, 255, 204)
SCHEDULER_TIME_LINE_COLOR = QtGui.QColor(227, 36, 43)
HYBRID_VIEW_SELECTION_COLOR = QtGui.QColor(227, 227, 43, 100)
HYBRID_VIEW_CONNECTION_LINE_COLOR = QtGui.QColor(227, 36, 43)

# Buttons
YES_BUTTON = QtWidgets.QMessageBox.StandardButton.Yes
NO_BUTTON = QtWidgets.QMessageBox.StandardButton.No
CANCEL_BUTTON = QtWidgets.QMessageBox.StandardButton.Cancel
