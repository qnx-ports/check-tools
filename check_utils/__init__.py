# PUBLIC
from .config import Config
from .junitxml import JUnitXML
from .definitions import IllegalArgumentError, InvalidSubprocessResultError,\
                CheckExit, BUILD_DIR, START_DIR, PACKAGE_CONFIG, PROJECT_CONFIG
from .test import GenericTest, TestGenerator, BinaryTest, ProjectTest
from .system_spec import SystemSpec
from .skipped import Skipped, SkippedCase, SkippedSuite
from .failed import FailedCase, FailedSuite
from .errored import ErroredCase, ErroredSuite
from .passed import PassedCase, PassedSuite

# PRIVATE
from .gtest import GTest
from .catch2test import Catch2Test
from .pytest import PyTest
from .mesontest import MesonTest

from typing import Final

TEST_FRAMEWORK_BUILTINS: Final[TestGenerator] = [
        GTest,
        Catch2Test,
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
        'PACKAGE_CONFIG',
        'PROJECT_CONFIG',
        'GenericTest',
        'TestGenerator',
        'BinaryTest',
        'ProjectTest',
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
        ]
