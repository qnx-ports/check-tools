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
Provides common base class definitions for creating test runner objects.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from functools import cache
import glob
import logging
from multiprocessing.pool import ThreadPool
import os
from pathlib import Path
import re
import subprocess
from typing import List, Optional, Generator, Set

from .config import Config
from .junitxml import JUnitXML
from .jtype.skipped import Skipped, SkippedSuite
from .system_spec import SystemSpec

class GenericTest(ABC):
    """
    Abstract class for a runnable test which produces a junit xml report file.
    """
    THEME_EXTENSIONS: dict = {
            "on_success": "bold green",
            "on_failure": "bold red",
            "on_stderr": "red"
        }

    def __init__(self):
        pass

    # --- PRIVATE ---
    @abstractmethod
    def _run_impl(self) -> str:
        """
        Run the impl object.

        @raise NotImplementedError: Called an abstract method.
        """
        raise NotImplementedError('_run_impl() not implemented!')

    @classmethod
    def _preprocess(cls, s: str) -> str:
        """
        Remove rich markup from string.
        """
        return re.sub(r'\[', r'\\[', s)

    @classmethod
    def _warn_partial_support(cls) -> None:
        logging.warning('%s is not yet fully supported! See '
                        'https://github.com/qnx-ports/check-tools?tab=readme-ov'
                        '-file#framework-support', cls.__name__)

    @classmethod
    def _info_cmd(cls, cmd: str) -> None:
        logging.info('%s running command: %s', cls.__name__,
                     cls._preprocess(cmd))

    @classmethod
    def _info_result(cls, cmd: str, res: subprocess.CompletedProcess) -> None:
        if res.returncode != 0:
            logging.info('%s command %s [on_failure]failed[/on_failure] with '
                         'status code %d (%s):\n%s\n[on_stderr]%s[on_stderr]',
                         cls.__name__, cls._preprocess(cmd),
                         res.returncode,
                         cls._preprocess(os.strerror(res.returncode)),
                         cls._preprocess(res.stdout),
                         cls._preprocess(res.stderr))
        else:
            logging.info('%s command %s '
                         '[on_success]succeeded[/on_success]:\n%s',
                         cls.__name__, cls._preprocess(cmd),
                         cls._preprocess(res.stdout))

    # --- PUBLIC ---
    def run(self) -> JUnitXML:
        """
        Run the tests and report the outcome.
        """
        return self._run_impl()

    def should_report_skipped_tests(self) -> bool:
        """
        Add skipped tests to the report if applicable.
        """
        pass

    @classmethod
    def log_support(cls) -> None:
        """
        Provide information about the level of support of the framework if
        applicable.
        """
        pass

class TestMeta:
    __test__ = False
    not_run: Set[str]
    skipped: List[SkippedSuite]

    """
    Metadata for a set of test jobs.

    Provides an interface for metadata on tests, shared between test instances.
    """
    def __init__(self, test_cls: type[GenericTest],
                 not_run: Set[str] = set(),
                 skipped: List[SkippedSuite] = []):
        self.test_cls = test_cls
        self.not_run = not_run
        self.skipped = skipped

    # --- PUBLIC ---
    def get_skipped(self) -> List[SkippedSuite]:
        return self.skipped

    def set_skipped(self, skipped: List[SkippedSuite]) -> None:
        self.skipped = skipped

    def extend_skipped(self, skipped: List[SkippedSuite]) -> None:
        self.skipped.extend(skipped)

    def add_skipped(self, skip_suite_obj: SkippedSuite) -> None:
        self.skipped.append(skip_suite_obj)

    def is_skipped(self, suite_name: str, case_name: str) -> bool:
        """
        Returns whether a particular test case is skipped.
        """
        skip_suite_obj = self._get_skipped_suite(suite_name)
        return (skip_suite_obj is not None) and  (skip_suite_obj.get_case(case_name) is not None)

    def add_not_run(self, binary) -> None:
        self.not_run.add(binary)

    def is_not_run(self, binary) -> bool:
        return binary in self.not_run

    def should_report_skipped_tests(self) -> bool:
        return self.test_cls.should_report_skipped_tests()

    # --- PRIVATE ---
    # Avoid iterating list when possible
    @cache
    def _get_skipped_suite(self, suite_name) -> SkippedSuite:
        for suite_iter in self.skipped:
            if suite_iter.get_name() == suite_name:
                return suite_iter
        return None

class TestJobset(ABC):
    meta: TestMeta
    tests: List[GenericTest]

    def __init__(self, meta: TestMeta, tests: List[GenericTest] = []):
        self.meta = meta
        self.tests = tests

    @abstractmethod
    def run(self, num_jobs) -> JUnitXML:
        raise NotImplementedError('run() not implemented!')

class BinaryTestJobset(TestJobset):
    def __init__(self, meta: TestMeta, tests: List[BinaryTest] = []):
        super().__init__(meta, tests)

    def run(self, num_jobs) -> JUnitXML:
        combined_xml = JUnitXML.make_from_passed([])

        if num_jobs > 1:
            with ThreadPool(processes=num_jobs) as pool:
                results = []
                for test in self.tests:
                    results.append(pool.apply_async(test.run))

                # Block until all threads terminate...
                for result in results:
                    combined_xml += result.get()
        else:
            for test in self.tests:
                combined_xml += test.run()

        if self.meta.should_report_skipped_tests():
            combined_xml += JUnitXML.make_from_skipped(self.meta.get_skipped())

        return combined_xml

class ProjectTestJobset(TestJobset):
    def __init__(self, meta: TestMeta, tests: List[ProjectTest] = []):
        super().__init__(meta, tests)

    def run(self, num_jobs) -> JUnitXML:
        combined_xml = JUnitXML.make_from_passed([])

        for test in self.tests:
            test.set_num_jobs(num_jobs)
            combined_xml += test.run()

        if self.meta.should_report_skipped_tests():
            combined_xml += JUnitXML.make_from_skipped(self.meta.get_skipped())

        return combined_xml

class TestGenerator(ABC):
    """
    Abstract class for a factory which produces test instances of the derived
    class.
    """
    # --- PUBLIC ---
    @classmethod
    @abstractmethod
    def make_test_jobset(
            cls,
            spec: SystemSpec,
            config: Config,
            ) -> Optional[TestJobset]:
        """
        Generate test instances.

        @yield a test instance.
        @raise NotImplementedError: Called an abstract method.
        """
        raise NotImplementedError('generate_test_list() not implemented!')

    @classmethod
    @abstractmethod
    def get_name_framework(cls) -> str:
        """
        Get the name of the test framework this class represents.

        @return the name of the framework.
        @raise NotImplementedError: Called an abstract method.
        """
        raise NotImplementedError('get_name_framework() not implemented!')

class BinaryTest(GenericTest, TestGenerator, ABC):
    """
    Abstract class for a factory which produces test instances of the derived
    class which correspond to a single executable binary file.
    """
    binary: str = ''
    opts: str = ''
    meta: TestMeta
    timeout: Optional[int] = None

    def __init__(self, binary: str, opts: str,
                 meta: TestMeta, timeout: Optional[int] = None):
        super().__init__()
        self.binary = binary
        self.opts = opts
        self.meta = meta
        self.timeout = timeout

    # --- PUBLIC ---
    @classmethod
    def make_test_jobset(
            cls,
            spec: SystemSpec,
            config: Config,
            ) -> Optional[TestJobset]:
        logging.debug('Generating binary test list for %s.',
                      cls.get_name_framework())
        tests: List[GenericTest] = []

        framework_config = config.get(cls.get_name_framework(), None)
        if framework_config is not None:
            cls.log_support()

            binaries: str = []
            for path in framework_config.get('path', '').splitlines():
                binaries.extend(p for p in glob.glob(path) if p not in binaries)

            meta = TestMeta(cls)
            for skip_iter in framework_config.get('skipped', []):
                skip_obj: Skipped = Skipped.make_from_dict(skip_iter)
                if skip_obj is not None:
                    if skip_obj.is_not_run():
                        meta.add_not_run(skip_obj.get_name())
                    else:
                        skipped = skip_obj.filter_tests(spec)
                        if skipped is not None:
                            meta.extend_skipped(skipped.get_suites())

            for binary in binaries:
                if meta.is_not_run(binary):
                    logging.debug('Skipping binary %s.', binary)
                    continue

                # Custom options
                # TODO: Optimize?
                common_opts: str = ''
                binary_opts: str = ''
                for opt_iter in framework_config.get('opt', []):
                    if opt_iter['name'] == 'common':
                        common_opts = opt_iter['opt']
                    elif Path(opt_iter['name']) == Path(binary):
                        binary_opts = opt_iter['opt']
                opts = f'{common_opts} {binary_opts}'

                tests.extend(cls._generate_test_list(binary, opts,
                                                   meta,
                                                   config.get('timeout', None)))
            return BinaryTestJobset(meta, tests)
        else:
            logging.debug('Could not find configuration for framework %s.',
                          cls.get_name_framework())
        return None

    # --- PRIVATE ---
    @classmethod
    def _generate_test_list(cls, binary: str, opts: str, meta: TestMeta,
                            timeout: Optional[int] = None) -> Generator[
                                    GenericTest, None, None]:
        """
        Generates tests on a file by file basis.
        By default forwards arguments to underlying constructor. Intended to be
        overriden to allow more granular jobs.
        """
        yield cls(binary, opts, meta, timeout)

class ProjectTest(GenericTest, TestGenerator, ABC):
    """
    Abstract class for a factory which produces test instances of the derived
    class which correspond to a project-level test runner.
    """
    path: str = ''
    opts: str = ''
    meta: TestMeta
    timeout: Optional[int] = None
    num_jobs: int

    def __init__(self, path: str, opts: str,
                 meta: TestMeta, timeout: Optional[int] = None):
        super().__init__()
        self.path = path
        self.opts = opts
        self.meta = meta
        self.timeout = timeout
        self.num_jobs = 1

    # --- PUBLIC ---
    @classmethod
    def make_test_jobset(
            cls,
            spec: SystemSpec,
            config: Config,
            ) -> Optional[TestJobset]:
        logging.debug('Generating project test list for %s.',
                      cls.get_name_framework())
        tests: List[GenericTest] = []

        framework_config = config.get(cls.get_name_framework(), None)
        if framework_config is not None:
            cls.log_support()

            path = framework_config.get('path', '')
            meta = TestMeta(cls)

            skipped = framework_config.get('skipped', None)
            if skipped is not None:
                for suite in skipped.get('suites', []):
                    skipped_suite = SkippedSuite.make_from_dict(suite)\
                            .filter_tests(spec)
                    if skipped_suite is not None:
                        meta.add_skipped(skipped_suite)

            opts = framework_config.get('opt', '')

            tests.append(cls(path, opts, meta,
                             config.get('timeout', None)))
            return ProjectTestJobset(meta, tests)
        else:
            logging.debug('Could not find configuration for framework %s.',
                          cls.get_name_framework())

        return None

    def set_num_jobs(self, num_jobs: int):
        self.num_jobs = num_jobs
