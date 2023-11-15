"""Constants for google dev workflow."""

import os

from scheduler.api.constants import SCHEDULER_PKG_DIR


# Token File
GOOGLE_TOKEN_FILE = os.path.join(SCHEDULER_PKG_DIR, "token.json")


# Calendar Dictionary Keys
CREATED_KEY = "created"
CREATOR_KEY = "creator"
END_KEY = "end"
START_KEY = "start"
DATE_KEY = "date"
DATE_TIME_KEY = "dateTime"
EVENT_TYPE_KEY = "eventType"
HTML_LINK_KEY = "htmlLink"
KIND_KEY = "kind"
EXTENDED_PROPERTIES_KEY = "extendedProperties"
SHARED_KEY = "shared"
SCHEDULER_ID_KEY = "id"
SYNCED_TO_SCHEDULER_KEY = "syncedToScheduler"
SUMMARY_KEY = "summary"


# Calendar Dictionary Values
DEFAULT_TYPE = "default"
CALENDAR_EVENT_KIND = "calendar#event"


# Calendar Ids
UK_HOLIDAYS_ID = "en.uk#holiday@group.v.calendar.google.com"


event = {
    # 'created': '2023-09-28T12:48:45.000Z',
    # 'creator': {'email': 'bencarey88@gmail.com', 'self': True},
    'end': {'date': '2023-10-09'},
    # 'etag': '"3391810651206000"',
    'eventType': 'default',
    # 'htmlLink': 'https://www.google.com/calendar/event?eid=MTN1MTh2ZXBqdmdibHJscmxqOHFkNWh1M3QgYmVuY2FyZXk4OEBt',
    # 'iCalUID': '13u18vepjvgblrlrlj8qd5hu3t@google.com',
    # 'id': '13u18vepjvgblrlrlj8qd5hu3t',
    'kind': 'calendar#event',
    # 'organizer': {'email': 'bencarey88@gmail.com', 'self': True},
    # 'reminders': {'useDefault': False},
    # 'sequence': 0,
    'start': {'date': '2023-10-08'},
    # 'status': 'confirmed',
    'summary': 'Test',
    # 'transparency': 'transparent',
    # 'updated': '2023-09-28T12:48:45.603Z'
}

