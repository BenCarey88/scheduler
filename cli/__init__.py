"""Commandline interface for launching scheduler application."""

import argparse

from scheduler.ui import run_application


def process_commandline():
    """Run application from command line."""
    run_application()
