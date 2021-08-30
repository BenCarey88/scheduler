"""Scheduler Qt application."""

import sys

from PyQt5 import QtCore, QtGui, QtWidgets


class SchedulerWindow(QtWidgets.QMainWindow):
    """Scheduler window class."""

    def __init__(self, *args, **kwargs):
        """Initialise main window."""
        super(QtWidgets.QMainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("Scheduler")
        self.resize(1600, 800)

        # central widget and overall layout
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QtWidgets.QHBoxLayout()
        self.central_widget.setLayout(self.layout)

        # outliner panel
        self.outliner_layout = QtWidgets.QVBoxLayout()
        self.layout.addLayout(self.outliner_layout)
        self.outliner_tree_view = QtWidgets.QTreeView()
        self.outliner_layout.addWidget(self.outliner_tree_view)

        # main view
        self.main_view_layout = QtWidgets.QVBoxLayout()
        self.layout.addLayout(self.main_view_layout)
        self.table = QtWidgets.QTableWidget(3, 10)
        self.main_view_layout.addWidget(self.table)


def run_application():
    """Open application window."""
    app = QtWidgets.QApplication(sys.argv)
    window = SchedulerWindow()
    window.show()
    app.exec_()
