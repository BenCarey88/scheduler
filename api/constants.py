"""Constants for scheduler api."""

import os

SCHEDULER_FILES_DIR = os.path.normpath(
    "/users/benca/OneDrive/Documents/pkgs-data/scheduler"
)
USER_PREFS_FILE = os.path.join(
    SCHEDULER_FILES_DIR, "user_prefs.json"
)

# this should be found from user prefs ideally
SCHEDULER_DIRECTORY = os.path.normpath(
    "/users/benca/OneDrive/Documents/Admin/scheduler"
)
SCHEDULER_TASKS_DIRECTORY = os.path.join(SCHEDULER_DIRECTORY, "tasks")
SCHEDULER_NOTES_FILE = os.path.join(SCHEDULER_DIRECTORY, "notes.txt")

SCHEDULER_AUTOSAVES_DIRECTORY = os.path.join(SCHEDULER_DIRECTORY, "_autosaves")
SCHEDULER_TASKS_AUTOSAVES_DIRECTORY = os.path.join(
    SCHEDULER_AUTOSAVES_DIRECTORY, "tasks"
)
