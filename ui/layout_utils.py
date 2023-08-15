"""Utility methods for laying out qt widgets."""

from PyQt5 import QtCore, QtGui, QtWidgets


def _layout_widgets(
        layout_or_widget,
        new_layout_type,
        *widgets,
        frame=False):
    """Create a layout of widgets and add to an existing layout or widget.

    Args:
        layout_or_widget (QLayout or QWidget): layout or widget to add to. If
            adding to a widget, and the layout of the widget already exists,
            add new_layout as a sublayout to it. Otheriwse, make new_layout the
            layout of the widget.
        new_layout_type (class): class of sublayout to put widgets in.
        widgets (list(QWidget)): widgets to add.
        frame (bool): if True, add a frame.

    Returns:
        (QBoxLayout): the layout for the widgets.
    """
    new_layout = new_layout_type()
    for widget in widgets:
        new_layout.addWidget(widget)
    frame_widget = None
    if frame:
        frame_widget = QtWidgets.QFrame()
        frame_widget.setLayout(new_layout)

    if isinstance(layout_or_widget, QtWidgets.QWidget):
        outer_layout = layout_or_widget.layout()
        if outer_layout is None:
            if frame_widget:
                outer_layout = new_layout_type()
            else:
                outer_layout = new_layout
                new_layout = None
            layout_or_widget.setLayout(outer_layout)

    elif isinstance(layout_or_widget, QtWidgets.QLayout):
        outer_layout = layout_or_widget

    else:
        raise ValueError(
            "layout_or_widget arg must be a layout or a widget, not "
            "{0}".format(type(layout_or_widget))
        )

    if frame_widget is not None:
        outer_layout.addWidget(frame_widget)
    elif new_layout is not None:
        outer_layout.addLayout(new_layout)

    return new_layout


def add_widgets_horizontally(layout_or_widget, *widget_list, frame=False):
    """Layout a list of widgets horizontally and add to an existing layout.

    Args:
        layout_or_widget (QLayout or QWidget): layout or widget to add to. If
            adding to a widget, and the layout of the widget already exists,
            add new_layout as a sublayout to it. Otheriwse, make new_layout the
            layout of the widget.
        widget_list (list(QWidget)): widgets to add.
        frame (bool): if True, add a frame.

    Returns:
        (QHBoxLayout): the horizontal layout.
    """
    return _layout_widgets(
        layout_or_widget,
        QtWidgets.QHBoxLayout,
        *widget_list,
        frame=frame,
    )


def add_widgets_vertically(layout_or_widgets, *widget_list, frame=False):
    """Layout a list of widgets vertically and add to an existing layout.

    Args:
        layout_or_widget (QLayout or QWidget): layout or widget to add to. If
            adding to a widget, and the layout of the widget already exists,
            add new_layout as a sublayout to it. Otheriwse, make new_layout the
            layout of the widget.
        widget_list (list(QWidget)): widgets to add.
        frame (bool): if True, add a frame.

    Returns:
        (QVBoxLayout): the vertical layout.
    """
    return _layout_widgets(
        layout_or_widgets,
        QtWidgets.QVBoxLayout,
        *widget_list,
        frame=frame,
    )


def layout_widget_dict(layout_or_widget, widget_list_or_dict):
    """Add widgets according to widget dict.

    Widget lists looks like this:
    [
        {
            # optional layout properties dict, eg.
            frame: True,
            orientation: vertical,
        },
        widget_1,
        widget_2,
        [
            # subdict or sublist representing widgets for sublayout
            widget_3_1,
            widget_3_2,
            ...
        ],
        ...
    ]

    Widget dicts looks like this:
    {
        # optionaly keyword args for layout properties, eg.
        frame: True,
        orientation: vertical,
        widget_1: {
            # widget properties dict, eg.
        },
        widget_2: None,  # represents no widget properties
        layout_1: {
            # subdict or sublist representing widgets for sublayout
            widget_3_1: {},
            ...
        },
        layout_name_2: {
            # as above, but to avoid having to manually create layouts,
            # you can just give an arbitrary name and then have them made for you
        }
        ...
    }

    Args:
        layout_or_widget (QLayout or QWidget): layout or widget to add to.
        widget_list_or_dict (list or OrderedDict): list or ordered dict of
            widgets to add. Can be nested, allowing sublayouts (and the nested
            elements can be either dicts or lists). See above for how they
            should be laid out. 
    """
    # ^TODO: maybe just delete this method because it's super gross?
    # or come up with a consistent way of doing it


def add_field_widget(vertical_layout, field_name, field_widget):
    """Add a label and widget representing a field and its value.

    Args:
        vertical_layout (QVBoxLayout): layout to add to.
        field_name (str): name of field that this widget edits.
        field_widget (QWidget): the widget that edits this field

    Returns:
        (QWidget): the field widget.
    """
    if not isinstance(vertical_layout, QtWidgets.QLayout):
        raise ValueError(
            "vertical_layout arg must be a QLayout object, not {0}".format(
                type(vertical_layout)
            )
        )
    label = QtWidgets.QLabel(field_name)
    add_widgets_horizontally(vertical_layout, label, field_widget)
    return field_widget


def add_checkbox_field(vertical_layout, field_name, default=False, **kwargs):
    """Add a label and checkbox widget.

    Args:
        vertical_layout (QVBoxLayout): layout to add to.
        field_name (str): name of field that this widget edits.
        default (boolean): default value of checkbox.
        kwargs (dict): kwargs to pass to add_field_widget.

    Returns:
        (QComboBox): the combobox widget.
    """
    checkbox = QtWidgets.QCheckBox()
    if default:
        checkbox.setChecked(True)
    return add_field_widget(vertical_layout, field_name, checkbox, **kwargs)


def add_text_field(vertical_layout, field_name, default=None, **kwargs):
    """Add a label and text widget.

    Args:
        vertical_layout (QVBoxLayout): layout to add to.
        field_name (str): name of field that this widget edits.
        default (str or None): if given, set as the combobox default value.
        kwargs (dict): kwargs to pass to add_field_widget.

    Returns:
        (QLineEdit): the line edit widget.
    """
    line_edit = QtWidgets.QLineEdit()
    if default is not None:
        line_edit.setText(default)
    return add_field_widget(vertical_layout, field_name, line_edit, **kwargs)


def add_combobox_field(
        vertical_layout,
        field_name,
        values,
        default=None,
        **kwargs):
    """Add a label and combobox widget.

    Args:
        vertical_layout (QVBoxLayout): layout to add to.
        field_name (str): name of field that this widget edits.
        values (iterable): the possible values of the combobox.
        default (str or None): if given, set as the combobox default value.
        kwargs (dict): kwargs to pass to add_field_widget.

    Returns:
        (QComboBox): the combobox widget.
    """
    combobox = QtWidgets.QComboBox()
    combobox.addItems(values)
    if default is not None:
        combobox.setCurrentText(default)
    return add_field_widget(vertical_layout, field_name, combobox, **kwargs)
