"""Functionality for syncing scheduled items with google calendar."""

# TODO: use my datetime wrapper instead (maybe just add a to_datettime func in)
import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from scheduler.api.calendar.scheduled_item import (
    ScheduledItem,
    ScheduledItemType,
)
from scheduler.api.common.date_time import Date, DateTime, Time

from . import constants


# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']


def setup_credentials():
    """Setup google api authorisation and credentials.

    Returns:
        (Credentials): credentials for using google calendar api.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(constants.GOOGLE_TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(
            constants.GOOGLE_TOKEN_FILE,
            SCOPES,
        )
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json",
                SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(constants.GOOGLE_TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    return creds


def scheduled_item_to_google_event(scheduled_item):
    """Convert scheduled item to google calendar event.

    Args:
        scheduled_item (ScheduledItem): scheduled item.

    Returns:
        (dict): google calendar event dict.
    """
    return {
        constants.START_KEY: {
            constants.DATE_TIME_KEY: scheduled_item.start_datetime,
        },
        constants.END_KEY: {
            constants.DATE_TIME_KEY: scheduled_item.end_datetime,
        },
        constants.EVENT_TYPE_KEY: constants.DEFAULT_TYPE,
        constants.KIND_KEY:  constants.CALENDAR_EVENT_KIND,
        constants.EXTENDED_PROPERTIES_KEY: {
            constants.SHARED_KEY: {
                constants.SCHEDULER_ID_KEY: None, # need way to generate a unique id
                constants.SYNCED_TO_SCHEDULER_KEY: True,
            }
        },
        constants.SUMMARY_KEY: scheduled_item.name,
    }


def google_event_to_scheduled_item(google_event, scheduler_calendar):
    """Convert scheduled item to google calendar event.

    Args:
        google_event (dict): google calendar event dict.
        scheduler_calendar (Calendar): the calendar.

    Returns:
        (ScheduledItem): scheduled item.
    """
    start_dict = google_event.get(constants.START_KEY, {})
    end_dict = google_event.get(constants.END_KEY, {})
    date = start_dict.get(constants.DATE_KEY)
    start_date_time = start_dict.get(constants.DATE_TIME_KEY)
    end_date_time = end_dict.get(constants.DATE_TIME_KEY)
    if date is not None:
        date = Date.from_isoformat(date)
    if start_date_time is not None:
        start_date_time = DateTime.from_isoformat(start_date_time) 
        date = start_date_time.date()
    if end_date_time is not None:
        end_date_time = DateTime.from_isoformat(end_date_time)

    # TODO: check if repeat, instance, etc.
    if start_date_time is not None and end_date_time is not None:
        return ScheduledItem(
            scheduler_calendar,
            start_date_time.time(),
            end_date_time.time(),
            date,
            item_type=ScheduledItemType.EVENT,
        )


def sync_scheduler_to_google_calendar(
        scheduler_calendar,
        credentials,
        date_range,
        include_repeat_items=True):
    """Sync calendar events from scheduler to google calendar.

    Args:
        scheduler_calendar (Calendar): the calendar.
        credentials (Credentials): google api credentials.
        date_range (tuple(Date, Date)): date to search for items within.
        include_repeat_items (bool): if True, sync repeat items as well.
    """
    # TODO: make get_events_in_range
    scheduled_items = scheduler_calendar.get_events_in_range(
        date_range,
        include_repeat_items=include_repeat_items,
    )
    google_events = [
        scheduled_item_to_google_event(scheduled_item)
        for scheduled_item in scheduled_items
    ]
    try:
        service = build('calendar', 'v3', credentials=credentials)
        all_google_calender_events = service.events()
        for event in google_events:
            all_google_calender_events.insert(
                calendarId='primary',
                body=event
            ).execute()

    except HttpError as error:
        print('An error occurred: %s' % error)


def sync_google_calendar_to_scheduler(
        credentials,
        date_range,
        scheduler_calendar,
        include_repeat_items=True):
    """Sync calendar events from scheduler to google calendar.

    Args:
        scheduler_calendar (Calendar): the scheduler calendar.
        credentials (Credentials): google api credentials.
        date_range (tuple(Date, Date)): date to search for items within.
        include_repeat_items (bool): if True, sync repeat items as well.
    """
    try:
        service = build('calendar', 'v3', credentials=credentials)

        now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        events_result = service.events().list(
            calendarId='primary',
            timeMin=date_range[0],
            timeMax=date_range[1],
            singleEvents=(not include_repeat_items),
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])

    except HttpError as error:
        print('An error occurred: %s' % error)

    scheduled_items = [
        google_event_to_scheduled_item(event) for event in events
    ]
    for scheduled_item in scheduled_items:
        scheduler_calendar.add_scheduled_item(scheduled_item)
