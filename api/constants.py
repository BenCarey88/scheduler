"""Constants for scheduler api."""

import os

SCHEDULER_FILES_DIR = os.path.normpath(
    "/users/benca/OneDrive/Documents/pkgs-data/scheduler"
)
USER_PREFS_FILE = os.path.join(
    SCHEDULER_FILES_DIR, "user_prefs.json"
)

# TODO: scheduler directory should be found from user prefs ideally
DEV_MODE = (os.getenv("DEV_MODE") == "on")
SCHEDULER_DIRECTORY = os.path.normpath(
    "/users/benca/OneDrive/Documents/Admin/Scheduler"
)
if DEV_MODE:
    SCHEDULER_DIRECTORY = os.path.normpath(
        "/users/benca/OneDrive/Documents/Admin/Scheduler_dev"
    )
TASKS_DIRECTORY = os.path.join(SCHEDULER_DIRECTORY, "tasks")
CALENDAR_DIRECTORY = os.path.join(SCHEDULER_DIRECTORY, "calendar")
TRACKER_FILE = os.path.join(SCHEDULER_DIRECTORY, "tracker.json")
NOTES_FILE = os.path.join(SCHEDULER_DIRECTORY, "notes.txt")

AUTOSAVES_DIRECTORY = os.path.join(SCHEDULER_DIRECTORY, "_autosaves")
TASKS_AUTOSAVES_DIRECTORY = os.path.join(AUTOSAVES_DIRECTORY, "tasks")
CALENDAR_AUTOSAVES_DIRECTORY = os.path.join(AUTOSAVES_DIRECTORY, "calendar")
TRACKER_AUTOSAVES_FILE = os.path.join(AUTOSAVES_DIRECTORY, "tracker.json")
NOTES_AUTOSAVES_FILE = os.path.join(AUTOSAVES_DIRECTORY, "notes.txt")
