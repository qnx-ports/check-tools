#
# Copyright (c) 2025, BlackBerry Limited. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

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

BUILD_DIR: Final[Path] = Path(os.getenv('BUILD_DIR'))\
        if os.getenv('BUILD_DIR') is not None\
        else Path.cwd().joinpath('build')

START_DIR: Final[Path] = Path(os.getenv('START_DIR'))\
        if os.getenv('START_DIR') is not None\
        else Path.cwd().joinpath('../..')

PROJECT_DIR: Final[Path] = Path(os.getenv('PROJECT_DIR'))\
        if os.getenv('PROJECT_DIR') is not None\
        else START_DIR.joinpath('../..')

PACKAGE_CONFIG: Final[Path] = Path(os.getenv('PACKAGE_CONFIG'))\
        if os.getenv('PACKAGE_CONFIG') is not None\
        else START_DIR.joinpath('test.toml')

PROJECT_CONFIG: Final[Path] = Path(os.getenv('PROJECT_CONFIG'))\
        if os.getenv('PROJECT_CONFIG') is not None\
        else PROJECT_DIR.joinpath('test.toml')
