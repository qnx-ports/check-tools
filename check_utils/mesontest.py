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
Provides definitions for running meson tests.
"""

import logging
import os
from pathlib import Path
import subprocess
from typing import List, Optional, Final

from .definitions import BUILD_DIR
from .junitxml import JUnitXML
from .skipped import SkippedSuite
from .test import ProjectTest
from .test import TestMeta

class MesonTest(ProjectTest):
    """
    Defines how to run and report a meson test.
    """
    XML_TEST_LOG: Final[Path] = Path('meson-logs/testlog.junit.xml')

    errored: List[str] = []
    tests: List[str] = []

    def __init__(self, path: str, output: str, opts: str,
                 meta: TestMeta, timeout: Optional[int] = None):
        super().__init__(path, output, opts, meta, timeout)

        # Meson doesn't have a way to exclude tests. We will need to filter
        # manually.
        command = f'meson test --list -C {BUILD_DIR}'
        logging.info('MesonTest running command: %s', command)
        status = None
        output = None
        status, output = subprocess.getstatusoutput(command)
        if status != 0:
            logging.error('Non-zero exit status %d '
                              'returned from %s', status,
                              command)
            raise subprocess.CalledProcessError('meson command failed.',
                                                cmd=command)

        logging.info('Parsing `meson test --list...`')
        self.tests = []
        for line in output.splitlines():
            logging.info('----------------------------------------------------')
            logging.info(line)
            # Meson cases either follow ` <project> / <test-name>` or '<test-name>'
            # format and are included in the test run via the test-name
            line = line.strip()
            if line.find('/') != -1:
                project, test = line.split('/', 1)
                project = project.strip()
                logging.info('project = %s', project)
            else:
                test = line
            test = test.strip()
            logging.info('test = %s', test)
            logging.info('----------------------------------------------------')

            self.tests.append(test)

    def _run_mesontest(self) -> None:
        skipped_tests = []
        if self.meta.get_skipped() is not None:
            for skip_obj in self.meta.get_skipped():
                for case in skip_obj.get_case_names():
                    case = case.strip()
                    if case.find('/') != -1:
                        _, test_name = case.split('/', 1)
                    else:
                        test_name = case
                    test_name = test_name.strip()
                    skipped_tests.append(test_name)

        run_tests = [test for test in self.tests if test not in skipped_tests]

        command = (f'meson test {" ".join(run_tests)} -C {BUILD_DIR} -j '
                   f'{self.num_jobs} {self.opts}')
        logging.info("MesonTest running command: %s", command)
        with open('/dev/null', 'w') as output_f:
            subprocess.run(
                    args=command,
                    stderr=output_f,
                    stdout=output_f,
                    timeout=self.timeout,
                    check=False,
                    shell=True
            )

        # Meson outputs as JUnit XML automatically.
        # FIXME: Not currently cleaning up test paths...
        report_xml = JUnitXML(file=BUILD_DIR.joinpath(self.XML_TEST_LOG))
        return report_xml

    @classmethod
    def should_report_skipped_tests(cls) -> None:
        return True

    @classmethod
    def get_name_framework(cls) -> str:
        return 'meson'

    _run_impl = _run_mesontest
