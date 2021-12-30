"""Constants for scheduler api."""

import os

SCHEDULER_FILES_DIR = os.path.normpath(
    "/users/benca/OneDrive/Documents/pkgs-data/scheduler"
)
USER_PREFS_FILE = os.path.join(
    SCHEDULER_FILES_DIR, "user_prefs.json"
)

# TODO: this should be found from user prefs ideally
# also remove the SCHEDULER_ prefix from most things
SCHEDULER_DIRECTORY = os.path.normpath(
    "/users/benca/OneDrive/Documents/Admin/scheduler"
)
SCHEDULER_TASKS_DIRECTORY = os.path.join(SCHEDULER_DIRECTORY, "tasks")
SCHEDULER_CALENDAR_DIRECTORY = os.path.join(SCHEDULER_DIRECTORY, "calendar")
SCHEDULER_NOTES_FILE = os.path.join(SCHEDULER_DIRECTORY, "notes.txt")

SCHEDULER_AUTOSAVES_DIRECTORY = os.path.join(SCHEDULER_DIRECTORY, "_autosaves")
SCHEDULER_TASKS_AUTOSAVES_DIRECTORY = os.path.join(
    SCHEDULER_AUTOSAVES_DIRECTORY, "tasks"
)
SCHEDULER_CALENDAR_AUTOSAVES_DIRECTORY = os.path.join(
    SCHEDULER_AUTOSAVES_DIRECTORY, "calendar"
)
