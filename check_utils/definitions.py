"""
Provides common definitions used by check-tools.
"""

from enum import IntEnum
from pathlib import Path
import os
from typing import Final

class IllegalArgumentError(RuntimeError):
    """
    Provided an illegal argument.
    """
    pass

class InvalidSubprocessResultError(RuntimeError):
    """
    Subprocess succeeded but gave a bad result.
    """
    pass

class CheckExit(IntEnum):
    """
    check.py program exit codes.
    """
    EXIT_SUCCESS = 0 # No failures or errors were found in the report.
    EXIT_FAILURE = 1 # At least one failure or error was found in the report.

PACKAGE_CONFIG: Final[Path] = Path(os.getenv('PACKAGE_CONFIG'))\
        if os.getenv('PACKAGE_CONFIG') is not None\
        else Path.cwd().joinpath('../config.toml')

PROJECT_CONFIG: Final[Path] = Path(os.getenv('PROJECT_CONFIG'))\
        if os.getenv('PROJECT_CONFIG') is not None\
        else Path.cwd().joinpath('../../../config.toml')

BUILD_DIR: Final[Path] = Path(os.getenv('BUILD_DIR'))\
        if os.getenv('BUILD_DIR') is not None\
        else Path.cwd().joinpath('build')
