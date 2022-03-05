"""Notes Tab."""

# TODO: no longer consistent with new project setup, either remove
# or add to project tree.

from PyQt5 import QtCore, QtGui, QtWidgets


from scheduler.api.constants import NOTES_FILE

from scheduler.ui.tabs.base_tab import BaseTab


class NotesTab(BaseTab):
    """Suggestions tab."""

    def __init__(self, tree_root, tree_manager, outliner, parent=None):
        """Setup suggestions tab main view.

        Args:
            tree_root (BaseTreeItem): tree root item for tab's models.
            tree_manager (TreeManager): tree manager object.
            outliner (Outliner): outliner widget.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(NotesTab, self).__init__(
            tree_root,
            tree_manager,
            outliner,
            parent=parent
        )
        self.text_edit = QtWidgets.QTextEdit(self)
        self.outer_layout.addWidget(self.text_edit)
        self.text_edit.setFontPointSize(12)
        try:
            with open(NOTES_FILE, "r") as file_:
                self.text_edit.setText(file_.read())
        except FileNotFoundError:
            pass

    def update(self):
        pass

    def save(self):
        with open(NOTES_FILE, "w+") as file_:
            file_.write(self.text_edit.toPlainText())
