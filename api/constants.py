"""Constants for scheduler api."""

import os

from .utils import OrderedStringEnum


# System and File
DEV_MODE = (os.getenv("DEV_MODE") == "on")
SCHEDULER_PKG_DIR = os.path.normpath(
    "/users/benca/OneDrive/Documents/pkg-data/Scheduler"
)
if DEV_MODE:
    SCHEDULER_PKG_DIR = os.path.normpath(
        "/users/benca/OneDrive/Documents/pkg-data/Scheduler_dev"
    )
USER_PREFS_FILE = os.path.join(SCHEDULER_PKG_DIR, "user_prefs.json")


# Global Enums
class TimePeriod(OrderedStringEnum):
    """Enum for different time periods."""
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"

class ItemStatus(OrderedStringEnum):
    """Enum for statuses of items."""
    UNSTARTED = "Unstarted"
    IN_PROGRESS = "In Progress"
    COMPLETE = "Complete"

class ItemSize(OrderedStringEnum):
    """Enum to store size types of items."""
    NONE = ""
    SMALL = "small"
    MEDIUM = "medium"
    BIG = "big"

class ItemImportance(OrderedStringEnum):
    """Enum to store levels of importance for items."""
    NONE = ""
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    CRITICAL = "critical"


# Hosted Data Container Pairing
PLANNER_TREE_PAIRING = "Planner_Tree_Pairing"
SCHEDULER_TREE_PAIRING = "Scheduler_Tree_Pairing"
PLANNER_SCHEDULER_PAIRING = "Planner_Scheduler_Pairing"
PLANNER_PARENT_CHILD_PAIRING = "Planner_Parent_Child_Pairing"


# TODO: this should DEFINITELY be set by user, as task attribute,
# hardcoding for now
TASK_COLORS = {
    "Projects": (255, 165, 0),                  # Orange
    "Work": (245, 245, 190),                    # Yellow
    "General To Do": (50,205,50),               # Green
    "Leisure And Learning": (255,192,203),      # Pink
    "Routines": (255,99,71),                    # Red
}
