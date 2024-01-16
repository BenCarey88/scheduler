"""Functionality for syncing scheduled items with google calendar."""

from __future__ import print_function

# TODO: use my datetime wrapper instead (maybe just add a to_datettime func in)
import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']


def setp_credentials():
    """Setup google api authourisation and credentials.

    Returns:
        (Credentials): credentials for using google calendar api.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json',
                SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        # TODO: this should be saved in pkg-data rather than in this file
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds


def scheduled_item_to_google_event(scheduled_item):
    """Convert scheduled item to google calendar event.

    Args:
        scheduled_item (ScheduledItem): scheduled item.

    Returns:
        (dict): google calendar event dict.
    """


def google_event_to_scheduled_item(google_event):
    """Convert scheduled item to google calendar event.

    Args:
        google_event (dict): google calendar event dict.

    Returns:
        (ScheduledItem): scheduled item.
    """


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
