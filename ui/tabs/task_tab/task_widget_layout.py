"""Custom layout class for task widgets."""

from PyQt5 import QtCore, QtGui, QtWidgets


class TaskWidgetLayout(QtWidgets.QVBoxLayout):
    """Layout used to store task and task category widgets."""
    SPACING = 40
    HEIGHT_BUFFER = 10
    RECOMMENDED_WIDTH = 1000

    def __init__(self, parent=None):
        """Initialize.

        Args:
            parent (QtWidgets.QWidget or None): parent widget, if exists.
        """
        super(TaskWidgetLayout, self).__init__(parent=parent)
        self._height = 0

    def add_widget(self, widget, index=None):
        """Add a widget and some spacing.

        Args:
            widget (QtWidgets.QWidget): the widget to add.
            index (int or None): the index of the tree item this corresponds
                to. If given, we add the item in the corresponding space in
                the tree.
        """
        num_widgets = self.count()
        if num_widgets == 0:
            if index is not None and index != 0:
                raise IndexError(
                    "Index {0} is too large for this layout".format(index)
                )
            self.addWidget(widget)
            self._height += widget.minimumHeight() + self.HEIGHT_BUFFER

        elif index is None:
            self.addSpacing(self.SPACING)
            self.addWidget(widget)
            self._height += (
                widget.minimumHeight() + self.HEIGHT_BUFFER + self.SPACING
            )

        else:
            widget_index = index * 2
            if widget_index < 0 or widget_index > num_widgets:
                raise IndexError(
                    "Index {0} is out of range for this layout".format(index)
                )
            if widget_index == 0:
                self.insertWidget(widget_index, widget)
                self.insertSpacing(widget_index, self.SPACING)
            else:
                self.insertSpacing(widget_index, self.SPACING)
                self.insertWidget(widget_index, widget)
            self._height += (
                widget.minimumHeight() + self.HEIGHT_BUFFER + self.SPACING
            )

    def remove_widget(self, widget):
        """Remove widget and associated spacing.

        Args:
            widget (QtWidgets.QWidget): the widget to remove.
        """
        num_widgets = self.count()
        index = self.indexOf(widget)
        if num_widgets == 1:
            spacer = None
        elif index == 0:
            spacer = self.itemAt(index + 1).widget()
        else:
            spacer = self.itemAt(index - 1).widget()

        self.removeWidget(widget)
        widget.deleteLater()
        self._height -= widget.minimumHeight() - self.HEIGHT_BUFFER
        if spacer:
            self.removeWidget(spacer)
            spacer.deleteLater()
            self._height -= self.SPACING

    @property
    def recommended_size(self):
        """Get recommended size for layout.

        Returns:
            (QtCore.QSize): recommended size.
        """
        return QtCore.QSize(self.RECOMMENDED_WIDTH, self._height)
