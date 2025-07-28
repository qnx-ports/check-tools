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

class MesonTest(ProjectTest):
    """
    Defines how to run and report a meson test.
    """
    XML_TEST_LOG: Final[Path] = Path('meson-logs/testlog.junit.xml')

    errored: List[str] = []
    tests: List[str] = []

    def __init__(self, output: str, opts: str,
                 skipped: List[SkippedSuite], timeout: Optional[int] = None):
        super().__init__(output, opts, skipped, timeout)

        # Meson doesn't have a way to exclude tests. We will need to filter
        # manually.
        command = 'meson test --list'
        logging.info('MesonTest running command: %s', command)
        status = None
        output = None
        status, output = subprocess.getstatusoutput(command)
        if not (os.WIFEXITED(status) and (os.WEXITSTATUS(status) == 0)):
            logging.error('Non-zero exit status %d '
                              'returned from %s', os.WEXITSTATUS(status),
                              command)
            raise subprocess.CalledProcessError('meson command failed.',
                                                cmd=command)

        logging.info('Parsing `meson test --list...`')
        self.tests = []
        for line in output.splitlines():
            logging.info('----------------------------------------------------')
            logging.info(line)
            # Meson cases follow the format `<project> / <test-name>` and are
            # included in the test run via the test-name.
            project, _, test = line.strip().split()
            logging.info('project = %s', project)
            logging.info('test = %s', test)
            logging.info('----------------------------------------------------')

            self.tests.append(test)

    def _run_mesontest(self) -> None:
        skipped_tests = []
        for skip_obj in self.meta.get_skipped():
            for case in skip_obj.get_case_names():
                _, _, test_name = case.strip().split()
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
        return False

    @classmethod
    def get_name_framework(cls) -> str:
        return 'meson'

    _run_impl = _run_mesontest
