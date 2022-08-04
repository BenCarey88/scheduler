"""Suggestions Tab."""

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.ui.tabs.base_tab import BaseTab


class SuggestionsTab(BaseTab):
    """Suggestions tab."""

    def __init__(self, project, parent=None):
        """Setup suggestions tab main view.

        Args:
            project (Project): the project we're working on.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(SuggestionsTab, self).__init__(
            "suggestions",
            project,
            parent=parent
        )
        self.view = QtWidgets.QWidget(self)
        self.outer_layout.addWidget(self.view)

    def update(self):
        pass
