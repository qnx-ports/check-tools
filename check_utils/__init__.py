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

# PUBLIC
from .config import Config
from .junitxml import JUnitXML
from .definitions import IllegalArgumentError, InvalidSubprocessResultError,\
                CheckExit, BUILD_DIR, START_DIR, PROJECT_DIR, PACKAGE_CONFIG,\
                PROJECT_CONFIG
from .test import GenericTest, TestGenerator, BinaryTest, ProjectTest,\
        TestJobset, TestMeta
from .system_spec import SystemSpec
from .jtype.skipped import Skipped, SkippedCase, SkippedSuite
from .jtype.failed import FailedCase, FailedSuite
from .jtype.errored import ErroredCase, ErroredSuite
from .jtype.passed import PassedCase, PassedSuite

from .plugin.html import output_html, show_html

# PRIVATE
from .framework.gtest import GTest
from .framework.catch2test import Catch2Test
from .framework.pytest import PyTest
from .framework.mesontest import MesonTest
from .framework.qttest import QtTest
from .framework.ctest import CTest

from typing import Final

TEST_FRAMEWORK_BUILTINS: Final[TestGenerator] = [
        GTest,
        Catch2Test,
        QtTest,
        CTest,
        PyTest,
        MesonTest
        ]

__all__ = [
        'Config',
        'JUnitXML',
        'IllegalArgumentError',
        'InvalidSubprocessResultError',
        'CheckExit',
        'TEST_FRAMEWORK_BUILTINS',
        'START_DIR',
        'BUILD_DIR',
        'PROJECT_DIR',
        'PACKAGE_CONFIG',
        'PROJECT_CONFIG',
        'GenericTest',
        'TestGenerator',
        'BinaryTest',
        'ProjectTest',
        'TestJobset',
        'TestMeta',
        'SystemSpec',
        'Skipped',
        'SkippedCase',
        'SkippedSuite',
        'FailedCase',
        'FailedSuite',
        'ErroredCase',
        'ErroredSuite',
        'PassedCase',
        'PassedSuite',
        'output_html',
        'show_html',
        ]
