"""Ui utility functions."""

from contextlib import contextmanager
import os

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.common.date_time import Date, Time


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
    QtGui.QGuiApplication.setOverrideCursor(cursor_type)
    try:
        yield
    finally:
        QtGui.QGuiApplication.restoreOverrideCursor()


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


def get_widget_value(widget):
    """Get the current value of a qt widget.

    Args:
        widget (QWidget): widget to read.

    Returns:
        (variant): current value of widget.
    """
    if isinstance(widget, QtWidgets.QLineEdit):
        return widget.text()

    elif isinstance(widget, QtWidgets.QComboBox):
        return widget.currentText()

    elif isinstance(widget, QtWidgets.QCheckBox):
        return widget.checkState()

    elif isinstance(widget, (QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox)):
        return widget.value()

    elif isinstance(widget, QtWidgets.QDateEdit):
        date = widget.date()
        return Date(date.year, date.month, date.day)
    
    elif isinstance(widget, QtWidgets.QTimeEdit):
        time = widget.time()
        return Time(time.hour, time.minute, time.second)

    raise ValueError(
        "get_widget_value method does not currently support widgets of "
        "type {0}".format(type(widget))
    )


def set_widget_value(widget, value):
    """Set the value of a qt widget.

    Args:
        widget (QWidget): widget to set.
        value (variant): value to set. Accepted values types will depend on
            the type of widget.

    Raises:
        (ValueError): if widget not accepted yet or value is not one that the
            widget can set.
    """
    if isinstance(widget, QtWidgets.QLineEdit):
        if isinstance(value, str):
            return widget.setText(value)

    elif isinstance(widget, QtWidgets.QComboBox):
        if isinstance(value, str):
            return widget.setCurrentText(value)

    elif isinstance(widget, QtWidgets.QCheckBox):
        if isinstance(value, bool):
            return widget.setChecked(value)
        elif isinstance(value, int):
            return widget.setCheckState(value)

    elif isinstance(widget, QtWidgets.QSpinBox):
        if isinstance(value, int):
            return widget.setValue(value)

    elif isinstance(widget, QtWidgets.QDoubleSpinBox):
        if isinstance(value, (float, int)):
            return widget.setValue(value)

    elif isinstance(widget, QtWidgets.QDateEdit):
        if isinstance(value, Date):
            return widget.setDate(
                QtCore.QDate(value.year, value.month, value.day)
            )
        elif isinstance(value, QtCore.QDate):
            return widget.setDate(value)

    elif isinstance(widget, QtWidgets.QTimeEdit):
        if isinstance(value, Time):
            return widget.setTime(
                QtCore.QTime(value.hour, value.minute, value.second)
            )
        elif isinstance(value, QtCore.QTime):
            return widget.setTime(value)

    else:
        raise ValueError(
            "set_widget_value method does not currently support widgets of "
            "type {0}".format(type(widget))
        )
    raise ValueError(
        "widget of type {0} cannot set values of type {1}".format(
            type(widget),
            type(value),
        )
    )


"""Id registry to store floating items by temporary ids."""
_TEMPORARY_ID_REGISTRY = {}
_GLOBAL_COUNT = 0


def generate_temporary_id(item):
    """Generate temporary id for item.

    Args:
        item (variant): item to generate id for.

    Returns:
        (str): id of item.
    """
    global _GLOBAL_COUNT
    id = str(_GLOBAL_COUNT)
    _GLOBAL_COUNT += 1
    _TEMPORARY_ID_REGISTRY[id] = item
    return id


def get_item_by_id(id, remove_from_registry=False):
    """Get item by id and remove from registry.

    Args:
        id (str): id of item to get.
        remove_from_registry (bool): if True, remove the item from
            the registry after returning it.

    Returns:
        (variant or None): item, if found.
    """
    item = _TEMPORARY_ID_REGISTRY.get(id, None)
    if remove_from_registry and item is not None:
        del _TEMPORARY_ID_REGISTRY[id]
    return item


def encode_mime_data(items, mime_data_format):
    """Encode items as mime data.

    Args:
        items (list(variant) or variant): items to encode.
        mime_data_format (str): format for mime data.

    Returns:
        (QtCore.QMimeData): the mimedata.
    """
    mimedata = QtCore.QMimeData()
    encoded_data = QtCore.QByteArray()
    stream = QtCore.QDataStream(encoded_data, QtCore.QIODevice.WriteOnly)

    if not isinstance(items, list):
        items = [items]
    if len(items) > 1:
        raise NotImplementedError(
            "Mime data currently only works for single item."
        )
    text = None
    for item in items:
        text = generate_temporary_id(item)
    if text:
        stream << QtCore.QByteArray(text.encode('utf-8'))
        mimedata.setData(mime_data_format, encoded_data)
    return mimedata


def decode_mime_data(mime_data, mime_data_format, drop=False):
    """Decode mime data.

    Args:
        mime_data (QtCore.QMimeData): the mime data to decode.
        mime_data_format (str or None): the format to decode.
        drop (bool): if True, this decoding is part of a drop action, meaning
            that we can delete the item's id after decoding.

    Returns:
        (variant or list(variant) or None): the encoded item/s, if found.
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
        encoded_id = bytes(byte_array).decode('utf-8')
    return get_item_by_id(encoded_id, remove_from_registry=drop)
