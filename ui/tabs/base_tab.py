"""Base tab widget for each of the main tabs"""


from PyQt5 import QtCore, QtGui, QtWidgets


class BaseTab(QtWidgets.QWidget):
    """Base tab widget that other tabs will inherit from.

    This will contain an outliner view and a main view.
    """
