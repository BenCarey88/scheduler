"""Constants for scheduler api."""

import os

SCHEDULER_FILES_DIR = os.path.normpath(
    "/users/benca/OneDrive/Documents/pkgs-data/scheduler"
)
USER_PREFS_FILE = os.path.join(
    SCHEDULER_FILES_DIR, "user_prefs.json"
)

# this should be found from user prefs ideally
SCHEDULER_TASKS_DIRECTORY = os.path.normpath(
    "/users/benca/OneDrive/Documents/Admin/scheduler/tasks"
)
