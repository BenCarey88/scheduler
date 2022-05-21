"""Ui utility functions."""

from contextlib import contextmanager
import os

from PyQt5 import QtCore, QtGui, QtWidgets


@contextmanager
def suppress_signals(*QObjects_list):
    """contextmanager to temporarily blocks all signals of passed QObjects.

    Args:
        QObjects_list (list(QtCore.QObject)) list of QObjects whose
            signals we want to block.
    """
    previous_state = {}
    for obj in QObjects_list:
        previous_state[obj] = obj.blockSignals(True)
    try:
        yield
    finally:
        for obj in QObjects_list:
            obj.blockSignals(previous_state[obj])


@contextmanager
def override_cursor(cursor_type):
    """contextmanager to temporarily set the cursor to a different type.

    Args:
        cursor_type (QtCore.Qt.CursorShape) Qt cursor to use.
    """
    QtGui.QApplication.setOverrideCursor(cursor_type)
    try:
        yield
    finally:
        QtGui.QApplication.restoreOverrideCursor()


def simple_message_dialog(message, informative_text=None, parent=None):
    """Launch simple message dialog with just yes, no options.

    Args:
        message (str): main message to display in message dialog.
        informative_text (str): optional additional message to display in
            dialog.
        Parent (QWidget or None): Qt widget to act as parent for dialog.

    Returns:
        (bool): True if user clicked 'Yes', False if user clicked 'No'.
    """
    message_dialog = QtWidgets.QMessageBox(parent)
    message_dialog.setText(message)
    if informative_text:
        message_dialog.setInformativeText(informative_text)
    message_dialog.setStandardButtons(
        message_dialog.StandardButton.Yes | message_dialog.StandardButton.No
    )
    return (message_dialog.exec() == message_dialog.StandardButton.Yes)


def custom_message_dialog(
        message,
        buttons,
        informative_text=None,
        parent=None):
    """Launch message dialog with custom buttons.

    Args:
        message (str): main message to display in message dialog.
        buttons (list(QtWidgets.QMessageBox.StandardButton)): buttons to use.
        informative_text (str): optional additional message to display in
            dialog.
        Parent (QWidget or None): Qt widget to act as parent for dialog.

    Returns:
        (QtWidgets.QMessageBox.StandardButton): which button was executed.
    """
    message_dialog = QtWidgets.QMessageBox(parent)
    message_dialog.setText(message)
    if informative_text:
        message_dialog.setInformativeText(informative_text)
    for button in buttons:
        message_dialog.addButton(button)
    return message_dialog.exec()


def set_style(widget, stylesheet_filename):
    """Set style from stylesheet.qss file on widget.

    Args:
        stylesheet_filename (str): name of stylesheet file under
            scheduler/ui/style directory. Can be in a subdirectory.
        widget (QtWidgets.QWidget): Qt widget to set style on.
    """
    stylesheet_path = os.path.join(
        os.path.dirname(__file__),
        "style",
        os.path.normpath(stylesheet_filename)
    )
    with open(stylesheet_path, "r") as stylesheet_file:
        stylesheet = stylesheet_file.read()
    widget.setStyleSheet(stylesheet)
