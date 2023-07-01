"""Outliner Panel, containing outliner and filter view."""

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.ui.dialogs import FilterDialog
from .filter_view import FilterView
from .outliner import Outliner


class OutlinerPanel(QtWidgets.QSplitter):
    """Outliner Panel, containing outliner and filter widget."""
    PANEL_KEY = "outliner_panel"
    SPLITTER_SIZES_PREF = "splitter_sizes"

    def __init__(self, tab, name, project, parent=None):
        """Initialise panel.

        Args:
            tab (BaseTab): tab this outliner is used for.
            name (str): name of tab (to pass to manager classes).
            project (Project): the project we're working on.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(OutlinerPanel, self).__init__(parent=parent)
        self.name = name
        self.tree_manager = project.get_tree_manager(name)
        self.user_prefs = project.user_prefs
        self.setOrientation(QtCore.Qt.Orientation.Vertical)
        self.outliner = Outliner(tab, self.tree_manager)
        self.filter_widget = FilterWidget(self.tree_manager, self.outliner)
        self.filter_view = self.filter_widget.filter_view
        self.addWidget(self.filter_widget)
        self.addWidget(self.outliner)

        self.splitterMoved.connect(self.on_splitter_moved)
        splitter_sizes = self.user_prefs.get_attribute(
            [self.name, self.PANEL_KEY, self.SPLITTER_SIZES_PREF]
        )
        if splitter_sizes:
            self.setSizes(splitter_sizes)

    def on_splitter_moved(self, new_pos, index):
        """Called when splitter is moved.

        Args:
            new_pos (int): new position of splitter.
            index (int): index of splitter moved.
        """
        self.user_prefs.set_attribute(
            [self.name, self.PANEL_KEY, self.SPLITTER_SIZES_PREF],
            [self.filter_widget.height(), self.outliner.height()]
        )

    def pre_edit_callback(self, callback_type, *args):
        """Callback for before an edit of any type is run.

        Args:
            callback_type (CallbackType): edit callback type.
            *args: additional args dependent on type of edit.
        """
        self.outliner.pre_edit_callback(callback_type, *args)

    def post_edit_callback(self, callback_type, *args):
        """Callback for after an edit of any type is run.

        Args:
            callback_type (CallbackType): edit callback type.
            *args: additional args dependent on type of edit.
        """
        self.outliner.post_edit_callback(callback_type, *args)
        self.filter_view.post_edit_callback(callback_type, *args)

    def on_tab_changed(self):
        """Callback for when we change to this tab.

        For speed purposes, some updates are done to all tabs (even inactive
        tabs) when editing, and some are only picked up when changing to
        that tab. This should be monitored and may need to change if we
        start to see lags either during edits or when changing tab.
        """
        self.outliner.on_tab_changed()
        self.filter_view.on_tab_changed()


class FilterWidget(QtWidgets.QWidget):
    """Filter widget containing filter view and button."""
    def __init__(self, tree_manager, outliner, parent=None):
        """Initialise widget.

        Args:
            tree_manager (TreeManager): tree manager object.
            outliner (Outliner): outliner view this filter applies to.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(FilterWidget, self).__init__(parent=parent)
        self.tree_manager = tree_manager
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)
        new_filter_button = QtWidgets.QPushButton("New filter")
        new_filter_button.clicked.connect(self.launch_filter_dialog)
        main_layout.addWidget(new_filter_button)
        self.filter_view = FilterView(tree_manager, outliner)
        main_layout.addWidget(self.filter_view)

    def sizeHint(self):
        """Get size hint.

        Returns:
            (QtCore.QSize): size hint.
        """
        return QtCore.QSize(0, self.filter_view.minimumHeight())

    def launch_filter_dialog(self):
        """Launch filter dialog."""
        FilterDialog(self.tree_manager).exec_()
