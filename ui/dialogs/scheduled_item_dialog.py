"""Scheduled item dialog for creating and editing scheduled items."""


from collections import OrderedDict
from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.common.date_time import Date, DateTime, Time, TimeDelta
from scheduler.api.calendar.repeat_pattern import RepeatPattern
from scheduler.api.calendar.scheduled_item import (
    ScheduledItem,
    ScheduledItemType,
)
from scheduler.api.enums import ItemUpdatePolicy

from scheduler.ui import utils
from .item_dialog import ItemDialog


class ScheduledItemDialog(ItemDialog):
    """Dialog for creating or editing scheduled items."""
    END_TIME_KEY = "End"
    START_TIME_KEY = "Start"

    def __init__(
            self,
            tree_manager,
            schedule_manager,
            scheduled_item=None,
            start_datetime=None,
            end_datetime=None,
            tree_item=None,
            planned_item=None,
            parent=None):
        """Initialise dialog.

        Args:
            tree_manager (TreeManager): the task tree manager object.
            calendar (calendar): the calendar object.
            scheduled_item (BaseScheduledItem or None): scheduled item we're
                editing, if this is in edit mode. If None, we're in create
                mode. Can be a single item or repeat item template.
            start_datetime (DateTime or None): start datetime to initialize
                with, if we're not passing a scheduled item.
            end_datetime (DateTime or None): end datetime to initialize with,
                with, if we're not passing a scheduled item.
            tree_item (Task or None): tree item to initialize with, if we're
                not passing a scheduled item.
            planned_item (PlannedItem or None): planned item parent for this
                scheduled item, if given.
            parent (QtWidgets.QWidget or None): parent widget, if one exists.
        """
        if (scheduled_item is None and 
                (start_datetime is None or end_datetime is None)):
            raise Exception(
                "Must either pass a scheduled item or start and end datetimes"
            )
        super(ScheduledItemDialog, self).__init__(
            tree_manager,
            "Scheduled Item",
            item=scheduled_item,
            tree_item=tree_item,
            parent=parent,
        )
        self._calendar = schedule_manager.calendar
        self._schedule_manager = schedule_manager
        self._planned_item = planned_item

        if scheduled_item is None:
            # create a temp scheduled item just to get default values
            scheduled_item = ScheduledItem(
                self._calendar,
                start_datetime.time(),
                end_datetime.time(),
                start_datetime.date(),
                tree_item=tree_item,
            )
        date = scheduled_item.date
        start_time = scheduled_item.start_time
        end_time = scheduled_item.end_time
        tree_item = scheduled_item.tree_item
        # get_repeat_pattern will return None for single items
        repeat_pattern = schedule_manager.get_repeat_pattern(scheduled_item)
        item_type = scheduled_item.type
        event_category = scheduled_item.category
        event_name = scheduled_item.name
        is_background = scheduled_item.is_background
        task_update_policy = scheduled_item.task_update_policy

        self.setMinimumSize(900, 700)
        utils.set_style(self, "scheduled_item_dialog.qss")

        self.cb_date = QtWidgets.QDateEdit()
        self.main_layout.addWidget(self.cb_date)
        self.cb_date.setDate(
            QtCore.QDate(date.year, date.month, date.day)
        )

        self.repeat_pattern_widget = RepeatPatternWidget(
            repeat_pattern,
            start_date=date,
        )
        self.main_layout.addWidget(self.repeat_pattern_widget)

        self.time_editors = {
            self.START_TIME_KEY: QtWidgets.QTimeEdit(),
            self.END_TIME_KEY: QtWidgets.QTimeEdit()
        }
        for name, time_editor in self.time_editors.items():
            layout = QtWidgets.QHBoxLayout()
            time_editor.setSizePolicy(
                QtWidgets.QSizePolicy.Expanding,
                QtWidgets.QSizePolicy.Fixed
            )
            time_editor.setMinimumSize(100, 30)
            label = QtWidgets.QLabel(name)
            label.setMinimumSize(100, 30)
            layout.addWidget(label)
            layout.addWidget(time_editor)
            self.main_layout.addLayout(layout)

        # TODO: can we find a way to avoid this? feels unneat
        if start_time >= Time(23, 59):
            start_time = Time(23, 59)
        if end_time >= Time(23, 59):
            end_time = Time(23, 59)
        self.time_editors[self.START_TIME_KEY].setTime(
            QtCore.QTime(start_time.hour, start_time.minute)
        )
        self.time_editors[self.END_TIME_KEY].setTime(
            QtCore.QTime(end_time.hour, end_time.minute)
        )
        self.main_layout.addSpacing(10)

        # TODO: create custom switcher widget and use that here
        # instead of tabs. (Like this):
        # [ (    )  TASK  ]
        # [ EVENT  (    ) ]
        # or maybe just with multiple buttons and one pressed down
        self.tab_widget = QtWidgets.QTabWidget()
        self.tab_widget.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred,
            QtWidgets.QSizePolicy.Policy.Maximum,
        )
        self.main_layout.addWidget(self.tab_widget)

        # Task Tab
        task_selection_tab = QtWidgets.QWidget()
        task_selection_layout = QtWidgets.QVBoxLayout()
        task_selection_tab.setLayout(task_selection_layout)
        self.tab_widget.addTab(task_selection_tab, "Task")

        self.task_label = QtWidgets.QLabel("")
        task_selection_layout.addStretch()
        task_selection_layout.addWidget(self.task_label)
        task_selection_layout.addStretch()

        task_update_layout = QtWidgets.QHBoxLayout()
        task_selection_layout.addLayout(task_update_layout)
        task_update_label = QtWidgets.QLabel("Task Update Policy")
        task_update_layout.addWidget(task_update_label)
        self.cb_task_update_policy = QtWidgets.QComboBox()
        self.cb_task_update_policy.addItems(
            ItemUpdatePolicy.get_task_policies()
        )
        self.cb_task_update_policy.setCurrentText(task_update_policy)
        task_update_layout.addWidget(self.cb_task_update_policy)
        task_selection_layout.addStretch()

        # Event Tab
        event_tab = QtWidgets.QWidget()
        event_layout = QtWidgets.QVBoxLayout()
        event_tab.setLayout(event_layout)
        self.tab_widget.addTab(event_tab, "Event")

        event_category_label = QtWidgets.QLabel("Category")
        self.event_category_line_edit = QtWidgets.QLineEdit()
        if event_category:
            self.event_category_line_edit.setText(event_category)
        event_name_label = QtWidgets.QLabel("Name")
        self.event_name_line_edit = QtWidgets.QLineEdit()
        if event_name:
            self.event_name_line_edit.setText(event_name)
        event_layout.addStretch()
        event_layout.addWidget(event_category_label)
        event_layout.addWidget(self.event_category_line_edit)
        event_layout.addStretch()
        event_layout.addWidget(event_name_label)
        event_layout.addWidget(self.event_name_line_edit)
        event_layout.addStretch()
        if item_type == ScheduledItemType.EVENT:
            self.tab_widget.setCurrentIndex(1)

        self.background_checkbox = QtWidgets.QCheckBox("Set as background")
        if is_background:
            self.background_checkbox.setCheckState(2)
        self.main_layout.addWidget(self.background_checkbox)
        self.background_checkbox.clicked.connect(
            self._configure_task_update_policy
        )

        self.tab_widget.currentChanged.connect(self.update)
        self.tree_view.selectionModel().currentChanged.connect(
            self.on_tree_view_changed
        )
        self.on_tree_view_changed()

    def on_tree_view_changed(self):
        """Callback for when a new tree item is selected."""
        if self.tree_item:
            self.task_label.setText(self.tree_item.path)
        self._configure_task_update_policy()

    @property
    def scheduled_item(self):
        """Get the scheduled item being edited, if one exists.

        Returns:
            (BaseScheduledItem or None): the scheduled item being edited,
                if one exists.
        """
        return self._item

    @property
    def start_time(self):
        """Get starting time for item, based on values set in editor.

        Returns:
            (DateTime): starting time.
        """
        time = self.time_editors[self.START_TIME_KEY].time()
        return Time(time.hour(), time.minute())

    @property
    def end_time(self):
        """Get end time for item, based on values set in editor.

        Returns:
            (DateTime): end time.
        """
        time = self.time_editors[self.END_TIME_KEY].time()
        return Time(time.hour(), time.minute())

    @property
    def date(self):
        """Get date for item, based on values set in editor.

        Returns:
            (Date): item date. This is either the date of the item, or,
                in the case of a repeat item, the date of the first instance
                of the item.
        """
        date = self.cb_date.date()
        return Date(date.year(), date.month(), date.day())

    @property
    def start_datetime(self):
        """Get starting datetime for item, based on values set in editor.

        Returns:
            (DateTime): starting datetime.
        """
        return DateTime.from_date_and_time(self.date, self.start_time)

    @property
    def end_datetime(self):
        """Get ending datetime for item, based on values set in editor.

        Returns:
            (DateTime): ending datetime.
        """
        return DateTime.from_date_and_time(self.date, self.end_time)

    @property
    def is_repeat(self):
        """Check if this is a repeating item.
        
        Returns:
            (bool): whether or not this is a repeating item.
        """
        return self.repeat_pattern_widget.is_enabled

    @property
    def repeat_pattern(self):
        """Get repeat pattern of item, if this is a repeating item.

        Returns:
            (RepeatPattern or None): repeat pattern, or None if
                this is not a repeat item, or if the pattern is invalid.
        """
        if self.is_repeat:
            return self.repeat_pattern_widget.get_repeat_pattern(self.date)
        return None

    @property
    def type(self):
        """Get type of scheduled item.

        Returns:
            (ScheduledItemType): type of item, based on current selected tab.
        """
        if self.tab_widget.currentIndex() == 1:
            return ScheduledItemType.EVENT
        return ScheduledItemType.TASK

    @property
    def category(self):
        """Get name of event category.

        Returns:
            (str): name of category.
        """
        if self.tab_widget.currentIndex() == 0:
            if self.tree_item:
                task = self.tree_item
                return task.top_level_task().name
            return ""
        else:
            return self.event_category_line_edit.text()

    @property
    def name(self):
        """Get name of scheduled item.

        Returns:
            (str): name of scheduled item.
        """
        if self.tab_widget.currentIndex() == 0:
            if self.tree_item:
                return self.tree_item.name
            return ""
        else:
            return self.event_name_line_edit.text()

    @property
    def task_update_policy(self):
        """Get task update policy.

        Returns:
            (ItemUpdatePolicy): task update policy.
        """
        return ItemUpdatePolicy(self.cb_task_update_policy.currentText())

    @property
    def is_background(self):
        """Return whether or not this item is a background item.

        Returns:
            (bool): whether or not this item is a background item.
        """
        return bool(self.background_checkbox.checkState())

    def _configure_task_update_policy(self):
        """Configure enabled/disabled state of task update policy combobox."""
        if (self.is_background or
                self._tree_manager.is_task_category(self.tree_item)):
            self.cb_task_update_policy.setEnabled(False)
        else:
            self.cb_task_update_policy.setEnabled(True)

    def _get_invalid_repeat_pattern_message(self):
        """Check if repeat pattern is invalid and return message if so.

        Returns:
            (str or None): message explaining why repeat pattern is invalid,
                if it is, else None.
        """
        if not self.is_repeat:
            return None
        repeat_pattern = self.repeat_pattern
        if repeat_pattern is None:
            return "Repeat pattern must include some days"
        if not repeat_pattern.check_end_date_validity():
            return "End date is too early - must be after all initial dates"

    def accept_and_close(self):
        """Run add or modify scheduled item edit.

        Called when user clicks accept.
        """
        message = self._get_invalid_repeat_pattern_message()
        if message is not None:
            utils.simple_message_dialog(
                "Repeat pattern given is invalid:\n\n{0}".format(message),
                parent=self
            )
            return
        if self.is_editor:
            # TODO: AT THE MOMENT MODIFYING REPEAT ITEMS IS DELETING ALL
            # OVERRIDES! fix this
            self._schedule_manager.modify_scheduled_item(
                self.scheduled_item,
                self.is_repeat,
                date=self.date,
                start_time=self.start_time,
                end_time=self.end_time,
                repeat_pattern=self.repeat_pattern,
                item_type=self.type,
                tree_item=self.tree_item,
                event_category=self.category,
                event_name=self.name,
                task_update_policy=self.task_update_policy,
                is_background=self.is_background,
            )
        else:
            if self.is_repeat:
                self._schedule_manager.create_repeat_scheduled_item(
                    self._calendar,
                    self.start_time,
                    self.end_time,
                    self.repeat_pattern,
                    item_type=self.type,
                    tree_item=self.tree_item,
                    event_category=self.category,
                    event_name=self.name,
                    task_update_policy=self.task_update_policy,
                    is_background=self.is_background,
                    planned_item=self._planned_item,
                )
            else:
                self._schedule_manager.create_scheduled_item(
                    self._calendar,
                    self.start_time,
                    self.end_time,
                    self.date,
                    item_type=self.type,
                    tree_item=self.tree_item,
                    event_category=self.category,
                    event_name=self.name,
                    task_update_policy=self.task_update_policy,
                    is_background=self.is_background,
                    repeat_pattern=self.repeat_pattern,
                    planned_item=self._planned_item,
                )
        super(ScheduledItemDialog, self).accept_and_close()

    def delete_item_and_close(self):
        """Run remove scheduled item edit.

        Called when user clicks delete.
        """
        self._schedule_manager.remove_scheduled_item(self.scheduled_item)
        super(ScheduledItemDialog, self).delete_item_and_close()


# TODO: update to allow non-week repeat patterns
# TODO: also this currently only allows single week gaps in patterns,
# update to allow multiple weeks, and different days for each one.
class RepeatPatternWidget(QtWidgets.QWidget):
    """Widget describing the repeat pattern."""

    def __init__(self, repeat_pattern=None, start_date=None, parent=None):
        """Initialise widget.

        Args:
            repeat_pattern (RepeatPattern or None): repeat pattern to
                initialise, if one already exists.
            start_date (Date or None): if given, and repeat pattern isn't,
                use this to set a lower bound on the end date.
            parent (QtWidgets.QWidget): parent widget, if one exists.
        """
        super(RepeatPatternWidget, self).__init__(parent=parent)
        # TODO: make separate stylesheet for this
        self.setStyleSheet(
            """
            QFrame {
                background-color: rgb(250, 250, 250);
                border-width: 1;
                border-radius: 3;
                border-style: solid;
                border-color: rgb(10, 10, 10);
            }
            """
        )
        outer_layout = QtWidgets.QVBoxLayout()
        self.setLayout(outer_layout)

        # Checkbox to enable/disable the framed subwidget
        self.enabled_checkbox = QtWidgets.QCheckBox("Repeat Instance")
        outer_layout.addWidget(self.enabled_checkbox)
        self.enabled_checkbox.stateChanged.connect(self.toggle_active_status)

        # Framed subwidget layout
        self.framed_widget = QtWidgets.QFrame()
        frame_layout = QtWidgets.QVBoxLayout()
        buttons_layout = QtWidgets.QHBoxLayout()
        frame_layout.addLayout(buttons_layout)
        self.framed_widget.setLayout(frame_layout)
        outer_layout.addWidget(self.framed_widget)

        # Weekday buttons
        self.weekday_buttons = OrderedDict()
        for day in Date.WEEKDAYS:
            weekday_button = QtWidgets.QPushButton(day[0])
            weekday_button.setMinimumWidth(30)
            weekday_button.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
            weekday_button.setCheckable(True)
            buttons_layout.addWidget(weekday_button)
            self.weekday_buttons[day] = weekday_button

        # Checkbox to enable/disable end date
        end_date_layout = QtWidgets.QHBoxLayout()
        end_date_layout.addStretch()
        frame_layout.addLayout(end_date_layout)
        self.end_date_enabled_checkbox = QtWidgets.QCheckBox("End Date")
        self.end_date_enabled_checkbox.stateChanged.connect(
            self.toggle_end_date_active_status
        )
        end_date_layout.addWidget(self.end_date_enabled_checkbox)

        # End date combobox
        self.cb_end_date = QtWidgets.QDateEdit()
        end_date_layout.addWidget(self.cb_end_date)
        end_date_enabled = (
            repeat_pattern is not None and repeat_pattern.end_date is not None
        )
        if end_date_enabled:
            self.end_date_enabled_checkbox.setCheckState(True)
            end_date = repeat_pattern.end_date
            self.cb_end_date.setDate(
                QtCore.QDate(end_date.year, end_date.month, end_date.day)
            )
        elif start_date is not None:
            next_week = (start_date + TimeDelta(weeks=1))
            self.cb_end_date.setDate(
                QtCore.QDate(next_week.year, next_week.month, next_week.day)
            )
        self.toggle_end_date_active_status(end_date_enabled)

        # Show or hide framed widget based on enabled checkbox
        enabled = (repeat_pattern is not None)
        if enabled:
            self.enabled_checkbox.setChecked(True)
            if repeat_pattern.repeat_type == repeat_pattern.WEEK_REPEAT:
                for date in repeat_pattern.initial_dates:
                    self.weekday_buttons[
                        date.weekday_string(short=False)
                    ].setChecked(True)
        self.toggle_active_status(enabled)

    def toggle_active_status(self, enabled):
        """Toggle active status of widget.

        Args:
            enabled (int): current state of checkbox widget, representing
                whether or not it is enabled.
        """
        self._is_enabled = bool(enabled)
        if enabled:
            self.framed_widget.show()
        else:
            self.framed_widget.hide()

    def toggle_end_date_active_status(self, enabled):
        """Toggle active status of end date edit box.

        Args:
            enabled (int): current state of end date checkbox widget,
                representing whether or not it is enabled.
        """
        self._end_date_enabled = bool(enabled)
        self.cb_end_date.setEnabled(enabled)

    @property
    def is_enabled(self):
        """Return whether or not widget is enabled.

        Returns:
            (bool): whether or not widget is enabled.
        """
        return self._is_enabled

    def get_repeat_pattern(self, date):
        """Get repeat pattern represented by widget.

        Args:
            date (Date): initial date for repeat pattern.

        Returns:
            (RepeatPattern or None): repeat pattern, or None
                if can't be made.
        """
        weekdays = [
            day for day, button in self.weekday_buttons.items()
            if button.isChecked()
        ]
        if not weekdays:
            return None
        end_date = None
        if self._end_date_enabled:
            end_date = self.cb_end_date.date()
            end_date = Date(end_date.year(), end_date.month(), end_date.day())

        return RepeatPattern.week_repeat(
            date,
            weekdays,
            end_date=end_date,
        )
