"""Commandline interface for launching scheduler application."""

import argparse

from scheduler.ui import run_application


def process_commandline():
    """Run application from command line."""
    parser = argparse.ArgumentParser(description='Scheduler Tool')
    parser.add_argument(
        "-p", "--project-dir",
        metavar="<path>",
        type=str,
        help=(
            "Project directory to use. Defaults to one saved in user "
            "prefs, or prompts user to save a new one if not found."
        ),
    )
    args = parser.parse_args()
    run_application(project=(args.project_dir or None))
