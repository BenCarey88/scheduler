"""Wrapper around datetime classes for easier interaction."""

from datetime import datetime, timedelta


class DateTime(datetime):
    """Datetime subclass with customised functions."""

    MON = "Monday"
    TUE = "Tuesday"
    WED = "Wednesday"
    THU = "Thursday"
    FRI = "Friday"
    SAT = "Saturday"
    SUN = "Sunday"
    WEEKDAYS = [MON, TUE, WED, THU, FRI, SAT, SUN]

    def __init__(self, *args, **kwargs):
        """Initialise datetime object."""
        super(DateTime, self).__init__(*args, **kwargs)
        self.num_weekdays = len(self.WEEKDAYS)

    @classmethod
    def date_time_from_string(cls, datetime_str):
        """Create datetime from string

        Args:
            datetime_str (str): date_time string in format:
                yyyy-mm-dd hh:mm:ss.ff

        Returns:
            (DateTime): datetime object.
        """
        return cls.strptime(
            datetime_str,
            "%Y-%m-%d %H:%M:%S.%f"
        )

    @classmethod
    def date_from_string(datetime_str):
        """Get datetime date object from string

        Args:
            datetime_str (str): date string in format:
                yyyy-mm-dd

        Returns:
            (DateTime): datetime object.
        """
        return datetime.datetime.strptime(
            datetime_str,
            "%Y-%m-%d"
        )

    @classmethod
    def time_from_string(cls, datetime_str):
        """Create datetime time object from string

        Args:
            datetime_str (str): time string in format:
                hh:mm:ss.ff

        Returns:
            (DateTime): datetime object.
        """
        return cls.strptime(
            datetime_str,
            "%H:%M:%S.%f"
        )

    def string(self):
        """Get string representing date_time.

        Returns:
            (str): datetime string.
        """
        return str(self)

    def date_string(self):
        """Get string representing date.

        Returns:
            (str): date string.
        """
        return str(self.date())

    def time_string(self):
        """Get string representing time.

        Returns:
            (str): time string.
        """
        return str(self.time())

    def weekday_string(self, short=True):
        """Get string representing weekday.

        Args:
            short (bool): if True, just return the three letter name.

        Returns:
            (str): weekday string.
        """
        weekday_string = self.WEEKDAYS[self.weekday()]
        return weekday_string[:3] if short else weekday_string
