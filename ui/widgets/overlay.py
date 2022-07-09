"""Overlay class for adding an overlay to another widget."""

from PyQt5 import QtCore, QtGui, QtWidgets


class OverlayedWidget(QtWidgets.QStackedWidget):
    """Stacked widget with overlay for custom drawing."""
    def __init__(self, sub_widget, parent=None):
        """Initialize.

        Args:
            sub_widget (QtWidgets.QWidget or None): widget to overlay.
            parent (QtWidgets.QWidget or None): widget parent.
        """
        super(OverlayedWidget, self).__init__(parent=parent)
        self.sub_widget = sub_widget
        self.overlay = Overlay()
        self.layout().setStackingMode(
            QtWidgets.QStackedLayout.StackingMode.StackAll
        )
        self.addWidget(self.overlay)
        self.addWidget(sub_widget)
        self.overlay.set_paint_function(self.paint_overlay)

    def sizeHint(self):
        """Get size hint for widget.

        Returns:
            (QtCore.QSize): size hint.
        """
        return self.sub_widget.sizeHint()

    def paint_overlay(self, painter):
        """Paint the overlay.

        Args:
            painter (QtGui.QPainter): the overlay painter.
        """
        pass


class Overlay(QtWidgets.QWidget):
    """Overlay widget for custom drawing."""
    def __init__(self, parent=None):
        """Initialize.

        Args:
            parent (QtWidgets.QWidget or None): widget parent.
        """
        super(Overlay, self).__init__(parent=parent)
        self.setAttribute(
            QtCore.Qt.WidgetAttribute.WA_NoSystemBackground
            )
        self.setAttribute(
            QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents
        )
        self.paint_function = None

    def set_paint_function(self, method):
        """Set a function to use when painting.

        Args:
            method (function): paint function. This must accept a single
                painter argument.
        """
        self.paint_function = method

    def paintEvent(self, event):
        """Override paint event to draw custom overlays.

        Args:
            event (QtCore.QEvent): the paint event.
        """
        super(Overlay, self).paintEvent(event)
        if self.paint_function is not None:
            painter = QtGui.QPainter(self)
            self.paint_function(painter)
