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


def encode_tree_mime_data(tree_items, mime_data_format):
    """Encode tree item/s as mimedata.

    Args:
        tree_items (list(BaseTreeItem) or BaseTreeItem): tree items to
            encode.
        mime_data_format (str or None): format for mime data.

    Returns:
        (QtCore.QMimeData): the mimedata.
    """
    mimedata = QtCore.QMimeData()
    if mime_data_format is None:
        return mimedata
    encoded_data = QtCore.QByteArray()
    stream = QtCore.QDataStream(encoded_data, QtCore.QIODevice.WriteOnly)

    if not isinstance(tree_items, list):
        tree_items = [tree_items]
    if len(tree_items) > 1:
        raise NotImplementedError(
            "Tree mime data currently only works for single item."
        )
    text = None
    for tree_item in tree_items:
        text = str(tree_item.internalPointer().path)
    if text:
        stream << QtCore.QByteArray(text.encode('utf-8'))
        mimedata.setData(mime_data_format, encoded_data)
    return mimedata


def decode_tree_mime_data(mime_data, mime_data_format, tree_manager):
    """Decode tree mime data.

    Args:
        mime_data (QtCore.QMimeData): the mime data to decode.
        mime_data_format (str or None): the format to decode.
        tree_manager (TreeManager): treee manager to use for decoding.

    Returns:
        (BaseTreeItem or list(BaseTreeItem) or None): the encoded tree
            item/s, if found.
    """
    if mime_data_format is None:
        return None
    encoded_data = mime_data.data(mime_data_format)
    stream = QtCore.QDataStream(encoded_data, QtCore.QIODevice.ReadOnly)
    if stream.atEnd():
        return False
    while not stream.atEnd():
        byte_array = QtCore.QByteArray()
        stream >> byte_array
        encoded_path = bytes(byte_array).decode('utf-8')
    return tree_manager.root.get_item_at_path(encoded_path)
