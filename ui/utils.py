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
            scheduler/ui/style directory. Can be in a subdirectory, in which
            case this arg should give the relative path to the file from the
            icons directory.
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


def get_qicon(icon_filename):
    """Get qicon from a given image file.

    Args:
        icon_filename (str): name of image file under scheduler/ui/icons
            directory. Can be in a subdirectory, in which case this arg
            should give the relative path to the file from the icons
            directory.

    Returns:
        (QtGui.QIcon): the qicon.
    """
    return QtGui.QIcon(
        os.path.join(
            os.path.dirname(__file__),
            "icons",
            os.path.normpath(icon_filename),
        )
    )


class BaseValueWidget(QtWidgets.QWidget):
    """Base class for any custom widget with getters and setters defined."""
    def get_value(self):
        raise NotImplementedError(
            "subclasses of BaseValueWidget must implement get_value"
        )
    def set_value(self, value):
        raise NotImplementedError(
            "subclasses of BaseValueWidget must implement set_value"
        )


class ValueWidgetWrapper(object):
    """Wrapper around qt widgets that represent a specific value."""
    def __init__(
            self,
            widget,
            getter=None,
            setter=None,
            default=None,
            add_to_layout=None):
        """Initialize struct.

        Args:
            widget (QtWidgets.QWidget): widget representing a value.
            getter (function or None): function to return the value. If not
                given, use the default.
            setter (function or None): function to set the value. If not
                given, use the default defined below.
            default (variant or None): if given, set the widget to this
                default value.
            add_to_layout (QtWidgets.QBoxLayout or None): if given, add
                the widget to the given layout.
        """
        self.widget = widget
        self.get_value = getter or get_widget_value_getter(widget)
        self.set_value = setter or get_widget_value_setter(widget)
        if default is not None:
            self.set_value(default)
        if add_to_layout is not None:
            add_to_layout.addWidget(widget)


class AttributeWidgetWrapper(ValueWidgetWrapper):
    """Wrapper around widgets that represent an attribute of an object."""
    def __init__(
            self,
            widget,
            attribute_name,
            attribute_getter,
            default_object=None,
            **kwargs):
        """Initialize struct.

        Args:
            widget (QtWidgets.QWidget): widget representing an attribute.
            attribute_name (str): name of attribute.
            attribute_getter (function): this function must accept a single
                argument which is the object whose attribute this widget
                represents, and it should return the value of this attribute
                on the object. This can be used to define default values on
                the widget.
            default_object (object or None): if given, set the default value
                of the widget based on the value of the attribute given.
            **kwargs: kwargs to pass to ValueWidgetWrapper init.
        """
        default = kwargs.get("default", None)
        if default is not None and default_object is not None:
            raise ValueError(
                "Cannot use both default and default_obejct args"
            )
        if default_object is not None:
            default = attribute_getter(default_object)
        super(AttributeWidgetWrapper, self).__init__(
            widget,
            **kwargs,
            default=default,
        )
        self.name = attribute_name
        self._attribute_getter = attribute_getter

    def get_attribute_value(self, object_):
        """Get value of attribute on object.
        
        Args:
            object_ (object): the object whose attribute this widget
                represents.

        Returns:
            (variant): the value of the attribute on the object.
        """
        return self._attribute_getter(object_)


def get_widget_value_getter(widget, raise_error=True):
    """Get a function to return the current value of a qt widget.

    If the widget inherits from BaseValueWidget, we always use the defined
    get_value method. Otherwise, we have several basic qt widget values
    defined here too.

    Args:
        widget (QWidget): widget that represents a value.
        raise_error (bool): if True, raise an error when widget not accepted.
            Otherwise, just return a getter that returns None.

    Raises:
        (ValueError): if widget type not accepted yet.

    Returns:
        (function): getter for widget. This function takes no args and
            returns the current value of the widget.
    """
    if isinstance(widget, BaseValueWidget):
        return widget.get_value

    elif isinstance(widget, QtWidgets.QLineEdit):
        return widget.text

    elif isinstance(widget, QtWidgets.QComboBox):
        return widget.currentText

    elif isinstance(widget, QtWidgets.QCheckBox):
        return widget.checkState

    elif isinstance(widget, (QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox)):
        return widget.value

    elif isinstance(widget, QtWidgets.QDateEdit):
        def getter():
            date = widget.date()
            return Date(date.year(), date.month(), date.day())
        return getter

    elif isinstance(widget, QtWidgets.QTimeEdit):
        def getter():
            time = widget.time()
            return Time(time.hour(), time.minute(), time.second())
        return getter

    if not raise_error:
        return lambda : None

    raise ValueError(
        "get_widget_value_getter method does not currently support widgets of "
        "type {0}".format(type(widget))
    )


def get_widget_value_setter(widget, raise_error=True):
    """Get a function to set the value of a qt widget.

    If the widget inherits from BaseValueWidget, we always use the defined
    get_value method. Otherwise, we have several basic qt widget values
    defined here too.

    Args:
        widget (QWidget): widget that represents a value.
        raise_error (bool): if True, raise an error when widget not accepted.
            Otherwise, just return a setter that does nothing.

    Raises:
        (ValueError): if widget not accepted yet.

    Returns:
        (function): setter for widget. This function takes one arg, the new
            value to set, and running it sets that value on the widget.
    """
    # helper functions    
    def value_error(value, widget):
        return ValueError(
            "Can't set value of type {0} on widget of type {1}".format(
                type(value),
                type(widget),
            )
        )
    def get_setter(setter_func, accepted_value_types):
        def setter(value):
            if isinstance(value, accepted_value_types):
                return setter_func(value)
            raise value_error(value, widget)
        return setter

    # find setters
    if isinstance(widget, BaseValueWidget):
        return widget.set_value

    elif isinstance(widget, QtWidgets.QLineEdit):
        return get_setter(widget.setText, str)

    elif isinstance(widget, QtWidgets.QComboBox):
        return get_setter(widget.setCurrentText, str)

    elif isinstance(widget, QtWidgets.QCheckBox):
        def setter(value):
            if isinstance(value, bool):
                return widget.setChecked(value)
            elif isinstance(value, int):
                return widget.setCheckState(value)
            raise value_error(value, widget)
        return setter

    elif isinstance(widget, QtWidgets.QSpinBox):
        return get_setter(widget.setValue, int)

    elif isinstance(widget, QtWidgets.QDoubleSpinBox):
        return get_setter(widget.setValue, (float, int))

    elif isinstance(widget, QtWidgets.QDateEdit):
        def setter(value):
            if isinstance(value, Date):
                return widget.setDate(
                    QtCore.QDate(value.year, value.month, value.day)
                )
            elif isinstance(value, QtCore.QDate):
                return widget.setDate(value)
            raise value_error(value, widget)
        return setter

    elif isinstance(widget, QtWidgets.QTimeEdit):
        def setter(value):
            if isinstance(value, Time):
                return widget.setTime(
                    QtCore.QTime(value.hour, value.minute, value.second)
                )
            elif isinstance(value, QtCore.QTime):
                return widget.setTime(value)
            raise value_error(value, widget)
        return setter

    if not raise_error:
        return lambda : None

    raise ValueError(
        "set_widget_value method does not currently support widgets of "
        "type {0}".format(type(widget))
    )


def get_widget_value(widget, raise_error=True):
    """Get the current value of a qt widget.

    Args:
        widget (QWidget): widget to read.
        raise_error (bool): if True, raise an error when widget not accepted.
            Otherwise, just return None

    Returns:
        (variant): current value of widget.
    """
    return get_widget_value_getter(widget, raise_error=raise_error)()


def set_widget_value(widget, value, raise_error=True):
    """Set the current value of a qt widget.

    Args:
        widget (QWidget): widget to read.
        value (variant): value to set. Accepted values types will depend on
            the type of widget.
        raise_error (bool): if True, raise an error when widget not accepted.
            Otherwise, just do nothing.
    """
    return get_widget_value_setter(widget, raise_error=raise_error)(value)


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
