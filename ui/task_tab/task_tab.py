"""TaskTab tab."""

from PyQt5 import QtCore, QtGui, QtWidgets

from ..base_tab import BaseTab
from .task_category_widget import TaskCategoryWidget

class TaskTab(BaseTab):
    """Task Tab main view."""

    def __init__(self, tree_root, parent=None):
        """Setup task main view.

        Args:
            tree_root (BaseTreeItem): tree root item for tab's models.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(TaskTab, self).__init__(tree_root, parent)
        self._fill_main_view()
        self._fill_scroll_area()

    def update(self):
        """Update view to sync with model.

        This is done by deleting and then recreating the scroll area and
        main view.
        """
        self.scroll_area.deleteLater()
        self._fill_main_view()
        self._fill_scroll_area()

    def _fill_main_view(self):
        """Fill main task view from tree root.

        This also sets the size on the view so that the scroll area can use
        it properly.
        """
        self.main_view = QtWidgets.QWidget()
        self.main_view_layout = QtWidgets.QVBoxLayout()
        self.main_view.setLayout(self.main_view_layout)

        minimum_height = 0
        for category in self.tree_root.get_all_children():
            widget = TaskCategoryWidget(
                category,
                tab=self,
                parent=self,
            )
            self.main_view_layout.addWidget(widget)
            minimum_height += widget.minimumHeight() + 10
        self.main_view.setMinimumSize(
            QtCore.QSize(1000, minimum_height)
        )

    def _fill_scroll_area(self):
        """Create scroll area and set its widget as main view."""
        self.scroll_area = QtWidgets.QScrollArea(self) 
        self.scroll_area.setBackgroundRole(QtGui.QPalette.ColorRole.Light)
        self.scroll_area.setWidget(self.main_view)
