
from PyQt5 import QtCore, QtGui, QtWidgets


class AddEventDialog(QtWidgets.QDialog):

    def __init__(self, start_time, end_time, date, parent=None):
        super(AddEventDialog, self).__init__(parent)

        flags = QtCore.Qt.WindowFlags(
            QtCore.Qt.WindowTitleHint | QtCore.Qt.WindowCloseButtonHint
        )
        self.setWindowFlags(flags)
        self.setMinimumSize(200, 100)

        self.setWindowTitle("Timetable Event Editor")
        outer_layout = QtWidgets.QVBoxLayout()
        self.setLayout(outer_layout)

        self.cb_date = QtWidgets.QDateEdit()
        outer_layout.addWidget(self.cb_date)
        self.cb_date.setDate(
            QtCore.QDate(date.year, date.month, date.day)
        )

        time_layout = QtWidgets.QHBoxLayout()
        outer_layout.addLayout(time_layout)
        self.cb_time_start = QtWidgets.QTimeEdit()
        self.cb_time_end = QtWidgets.QTimeEdit()
        time_layout.addWidget(QtWidgets.QLabel("Start"))
        time_layout.addWidget(self.cb_time_start)
        time_layout.addSpacing(50)
        time_layout.addWidget(QtWidgets.QLabel("End"))
        time_layout.addWidget(self.cb_time_end)
        # 23.98 =~ 59/60
        # TODO: this should be way neater
        if int(start_time) >= 23.99:
            start_time = 23.99
        if int(end_time) >= 23.99:
            end_time = 23.99
        self.cb_time_start.setTime(
            QtCore.QTime(
                int(start_time),
                (start_time % 1) * 60,
            )
        )
        self.cb_time_end.setTime(
            QtCore.QTime(
                int(end_time),
                (end_time % 1) * 60,
            )
        )

        self.add_event_button = QtWidgets.QPushButton("Add Event")
        outer_layout.addWidget(self.add_event_button)
        self.add_event_button.clicked.connect(self.accept_and_close)

    @staticmethod
    def qtime_to_float(qtime):
        return qtime.hour() + qtime.minute() / 60

    @property
    def start_time(self):
        return self.qtime_to_float(self.cb_time_start.time())

    @property
    def end_time(self):
        return self.qtime_to_float(self.cb_time_end.time())

    @property
    def category(self):
        return "Category"

    @property
    def name(self):
        return "Name"

    def accept_and_close(self):
        self.accept()
        self.close()
