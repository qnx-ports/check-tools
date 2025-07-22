"""
Provides definitions for running meson tests.
"""

import logging
import os
from pathlib import Path
import subprocess
from typing import List, Optional, Final

from .test import ProjectTest
from .skipped import SkippedSuite
from .definitions import BUILD_DIR
from .junitxml import JUnitXML

class MesonTest(ProjectTest):
    """
    Defines how to run and report a meson test.
    """
    XML_TEST_LOG: Final[Path] = Path('meson-logs/testlog.junit.xml')

    errored: List[str] = []
    tests: List[str] = []

    def __init__(self,
                 path: str, report: str, output: str, opts: str,
                 skipped: List[SkippedSuite], timeout: Optional[int] = None):
        super().__init__(path, report, output, opts, skipped, timeout)

        # Meson doesn't have a way to exclude tests. We will need to filter
        # manually.
        command = f'meson test -C {BUILD_DIR} --list'
        logging.info('MesonTest running command: %s', command)
        status = None
        output = None
        status, output = subprocess.getstatusoutput(command)
        if status:
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
                project, test = line.split('/')
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
        for skip_obj in self.skipped:
            for case in skip_obj.get_case_names():
                test_name = case.strip()
                skipped_tests.append(test_name)

        run_tests = [test for test in self.tests if test not in skipped_tests]

        command = f'meson test {" ".join(run_tests)} -C {BUILD_DIR} {self.opts}'
        logging.info("MesonTest running command: %s", command)
        with open(self.get_output(), 'a', encoding="utf-8") as output_f:
            subprocess.run(
                    args=command,
                    stderr=output_f,
                    stdout=output_f,
                    timeout=self.timeout,
                    check=False,
                    shell=True
            )

        # Meson outputs as JUnit XML automatically. We just need to rename it so
        # that the rest of the program can find it.
        BUILD_DIR.joinpath(self.XML_TEST_LOG).rename(self.report)

    def _report_skipped_tests(self) -> None:
        if len(self.skipped) != 0:
            report_xml = JUnitXML(file=self.report)

            skipped_xml = JUnitXML.make_from_skipped(self.skipped)

            report_xml += skipped_xml

            report_xml.write(self.report)

    @classmethod
    def get_name_framework(cls) -> str:
        return 'meson'

    _run_impl = _run_mesontest
