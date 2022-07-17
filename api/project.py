"""Class representing a full scheduler project."""

import os

from .common.user_prefs import ProjectUserPrefs
from .managers import ScheduleManager, PlannerManager, TreeManager
from .serialization.serializable import (
    CustomSerializable,
    SaveType,
    SerializableFileTypes,
    SerializationError,
)
from .serialization import file_utils
from .calendar import Calendar, Tracker
from .tree import TaskRoot
from .utils import backup_git_repo


class ProjectTree(object):
    """Struct used to get file and directory paths for a scheduler project.

    This struct is also used by subtrees within the project, eg. the archive
    and autosaves directories in a directory tree will also contain several
    of the same subdirectories and files as the project base, so can make use
    of the same struct.
    """
    AUTOSAVES_DIR_NAME = "_autosaves"
    ARCHIVE_DIR_NAME = "archive"
    TASK_DIR_NAME = "tasks"
    CALENDAR_DIR_NAME = "calendar"
    TRACKER_FILE_NAME = "tracker.json"
    # NOTES_FILE_NAME = "notes.txt"
    USER_PREFS_FILE_NAME = "user_prefs.json"

    def __init__(self, project_root_path):
        """Initialize struct.

        Args:
            project_root_path (str): path to root of project.
        """
        self._project_root_path = project_root_path

    @property
    def root_directory(self):
        """Return root directory path.

        Returns:
            (str): path to project root directory.
        """
        return self._project_root_path

    @property
    def autosaves_directory(self):
        """Get directory for autosaves to go into.

        Returns:
            (str): path to project autosaves directory.
        """
        return os.path.join(self._project_root_path, self.AUTOSAVES_DIR_NAME)

    @property
    def autosaves_tree(self):
        """Get project tree for autosaves directory.

        Returns:
            (ProjectTree): project tree for autosaves directory.
        """
        return ProjectTree(self.autosaves_directory)

    @property
    def archive_directory(self):
        """Get directory for archived items.

        Returns:
            (str): path to archive directory.
        """
        return os.path.join(self._project_root_path, self.ARCHIVE_DIR_NAME)

    @property
    def archive_tree(self):
        """Get project tree for autosaves directory.

        Returns:
            (ProjectTree): project tree for autosaves directory.
        """
        return ProjectTree(self.archive_directory)

    @property
    def tasks_directory(self):
        """Get directory for tasks.

        Returns:
            (str): path to tasks directory.
        """
        return os.path.join(self._project_root_path, self.TASK_DIR_NAME)

    @property
    def calendar_directory(self):
        """Get directory for calendar items.

        Returns:
            (str): path to calendar directory.
        """
        return os.path.join(self._project_root_path, self.CALENDAR_DIR_NAME)

    @property
    def tracker_file(self):
        """Get file path for tracker.

        Returns:
            (str): path to tracker file.
        """
        return os.path.join(self._project_root_path, self.TRACKER_FILE_NAME)

    # @property
    # def notes_file(self):
    #     """Get file path for notes.

    #     Returns:
    #         (str): path to tracker file.
    #     """
    #     return os.path.join(self._project_root_path, self.NOTES_FILE_NAME)

    @property
    def project_user_prefs_file(self):
        """Get file path for project user prefs.

        Returns:
            (str): path to project user prefs file.
        """
        return os.path.join(self._project_root_path, self.USER_PREFS_FILE_NAME)


class Project(CustomSerializable):
    """Class representing a full scheduler project.

    A project consists of the following components, each of which is
    represented by a separate serializable class:
        - Tasks
        - Calendar
        - Tracker

    A project also includes the following data (which aren't considered
    components):
        - Autosaves subtree
        - Archive subtree
        - User preferences
    """
    _SAVE_TYPE = SaveType.DIRECTORY
    _STORE_SAVE_PATH = True
    _MARKER_FILE = "scheduler_project{0}".format(SerializableFileTypes.MARKER)

    def __init__(self, project_root_path):
        """Initialize project.

        Currently a project needs a directory path in order to be started.
        In theory we could leave it until save time to set this path, although
        this would mean we no longer have autosaves for the duration of that
        session (and I don't think it's an issue to ask the user to set the
        directory first).

        Args:
            project_root_path (str): path to root of project.
        """
        self.set_project_path(project_root_path)
        self._load_project_data()
        self._tree_managers = {}
        self._schedule_manager = None
        self._planner_manager = None

    def set_project_path(self, project_root_path):
        """Set project path to given directory.

        Args:
            project_root_path (str): path to root of project.
        """
        file_utils.check_directory_can_be_written_to(
            project_root_path,
            self._MARKER_FILE
        )
        self.set_save_path(project_root_path)
        self._project_tree = ProjectTree(project_root_path)
        self._autosaves_tree = self._project_tree.autosaves_tree
        self._archive_tree = self._project_tree.archive_tree

    def _load_project_data(self):
        """Load all project classes from files."""
        self._task_root = TaskRoot.safe_read(
            self._project_tree.tasks_directory,
        )
        self._calendar = Calendar.safe_read(
            self._project_tree.calendar_directory,
            self._task_root,
        )
        self._tracker = Tracker.safe_read(
            self._project_tree.tracker_file,
            self._task_root,
        )
        self._user_prefs = ProjectUserPrefs.safe_read(
            self._project_tree.project_user_prefs_file,
            self._task_root,
        )
        # Archive
        # TODO: calendar and tracker need to init with task archive too
        self._archive_task_root = TaskRoot.safe_read(
            self._archive_tree.tasks_directory,
        )
        self._archive_calendar = Calendar.safe_read(
            self._archive_tree.calendar_directory,
            self._task_root,
        )

    @property
    def root_directory(self):
        """Get project root directory

        Returns:
            (str): project root directory.
        """
        return self._project_tree.root_directory

    # TODO: make consistent across repo 'tree root' /'task root'
    @property
    def task_root(self):
        """Get task root component.

        Returns:
            (TaskRoot): task root object.
        """
        return self._task_root

    @property
    def calendar(self):
        """Get calendar component.

        Returns:
            (TaskRoot): calendar object.
        """
        return self._calendar

    @property
    def tracker(self):
        """Get tracker component.

        Returns:
            (Tracker): tracker object.
        """
        return self._tracker

    @property
    def archive_task_root(self):
        """Get archive task root.

        Returns:
            (TaskRoot): archived task root object.
        """
        return self._archive_task_root

    @property
    def archive_calendar(self):
        """Get archive calendar.

        Returns:
            (Calendar): archived calendar object.
        """
        return self._archive_calendar

    @property
    def user_prefs(self):
        """Get project user prefs.

        Returns:
            (ProjectUserPrefs): user prefs object.
        """
        return self._user_prefs

    def get_tree_manager(self, name):
        """Get a tree manager for this project with the given name.

        Args:
            name (str): name of manager object.

        Returns:
            (TreeManager): tree manager for managing tree edits and filtering.
        """
        if self._tree_managers.get(name) is None:
            self._tree_managers[name] = TreeManager(
                name,
                self.user_prefs,
                self.task_root,
                self.archive_task_root,
            )
        return self._tree_managers.get(name)

    def get_schedule_manager(self):
        """Get calendar manager for this project.

        Returns:
            (ScheduleManager): calendar manager for managing calendar edits
                and filtering.
        """
        if self._schedule_manager is None:
            self._schedule_manager = ScheduleManager(
                self.user_prefs,
                self.calendar,
                self.archive_calendar,
            )
        return self._schedule_manager

    def get_planner_manager(self):
        """Get calendar manager for this project.

        Returns:
            (PlannerManager): planner manager for managing planner edits
                and filtering.
        """
        if self._planner_manager is None:
            self._planner_manager = PlannerManager(
                self.user_prefs,
                self.calendar,
                self.archive_calendar,
            )
        return self._planner_manager

    # TODO: find a way to avoid writing entire tree, should be able to just
    # save edited components
    def _write_all_components(self, project_tree):
        """Write all components to the given project tree.

        Args:
            project_tree (str): project tree to write to.
        """
        self._task_root.write(project_tree.tasks_directory)
        self._calendar.write(project_tree.calendar_directory)
        self._tracker.write(project_tree.tracker_file)

    @classmethod
    def from_directory(cls, project_root_path):
        """Read project from directory path.

        Args:
            project_root_path (str): path to root of project.

        Returns:
            (Project): class instance.
        """
        is_project_dir = file_utils.is_serialize_directory(
            project_root_path,
            cls._MARKER_FILE
        )
        if not is_project_dir:
            raise SerializationError(
                "Directory {0} is not a scheduler project ".format(
                    project_root_path
                )
            )
        return cls(project_root_path)

    def to_directory(self, directory_path):
        """Write project to directory path.

        Args:
            directory_path (str): path to directory to write to.
        """
        file_utils.check_directory_can_be_written_to(
            directory_path,
            self._MARKER_FILE
        )
        if not os.path.exists(directory_path):
            os.mkdir(directory_path)
            with open(os.path.join(directory_path, self._MARKER_FILE), "w+"):
                pass
        self._write_all_components(self._project_tree)

    def autosave(self):
        """Write project files to autosaves directory."""
        if not os.path.exists(self._autosaves_tree.root_directory):
            os.mkdir(self._autosaves_tree.root_directory)
        self._write_all_components(self._autosaves_tree)

    def write_user_prefs(self):
        """Write project user prefs file."""
        self._user_prefs.write(self._project_tree.project_user_prefs_file)

    def git_backup(self):
        """Backup project data with git push.

        Returns:
            (str or None): error message, if an error occurred.
        """
        return backup_git_repo(self.root_directory)
