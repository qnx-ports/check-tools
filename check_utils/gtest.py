"""
Provides definitions for running googletest tests.
"""

import datetime
import logging
import os
from pathlib import Path
import subprocess
import tempfile
from typing import List, Optional, Tuple

from .test import BinaryTest
from .skipped import Skipped
from .errored import ErroredCase, ErroredSuite
from .junitxml import JUnitXML

class GTest(BinaryTest):
    """
    Defines how to run and report a googletest test.
    """
    tests: List[Tuple[str, List[str]]] = []
    skipped_tests: List[str] = []
    errored: List[ErroredSuite] = []
    errored_tests: List[str] = []

    def __init__(self, binary: str,
                 report: str, output: str, opts: str,
                 skipped: Optional[Skipped], timeout: Optional[int] = None):
        super().__init__(binary, report, output, opts, skipped, timeout)

        # Googletest uniquely identifies tests with the pattern `<suite>.<case>`
        self.skipped_tests = []
        if self.skipped is not None:
            for suite in self.skipped.get_suites():
                self.skipped_tests += [suite.get_name() + '.' + case_name
                                       for case_name in suite.get_case_names()]

        # Run test cases individually so we can catch an error.
        command = f'./{self.binary} --gtest_list_tests'
        logging.info('GTest running command: %s', command)
        status = None
        output = None
        status, output = subprocess.getstatusoutput(command)
        if not (os.WIFEXITED(status) and (os.WEXITSTATUS(status) == 0)):
            logging.error('Non-zero exit status %d '
                              'returned from %s', os.WEXITSTATUS(status),
                              command)
            raise subprocess.CalledProcessError('googletest command failed.',
                                                cmd=command)

        suite = ''
        cases = []
        self.tests = []
        for line in output.splitlines():
            stripped = line.strip()
            if ' ' not in stripped and stripped.endswith('.'):
                # Suite identifier.

                # Add the old suite to result.
                if len(suite) != 0:
                    self.tests.append((suite, cases))
                    cases = []
                # Update suite.
                suite = stripped[:-1]
            elif len(suite) != 0 and line.startswith(' '):
                # Case identifier.
                case = stripped
                case_full = suite + '.' + case

                if case_full not in self.skipped_tests:
                    cases.append(case)
        # Add last suite in output.
        if len(suite) != 0:
            self.tests.append((suite, cases))

    def _run_gtest(self) -> None:
        report_xml = JUnitXML()
        with open(self.get_output(), 'a', encoding="utf-8") as output_f:
            for suite, cases in self.tests:
                # Suite timestamp
                timestamp = datetime.datetime.now().isoformat()

                errored_cases = []
                for case in cases:
                    case_full = suite + '.' + case

                    f, tmp_report = tempfile.mkstemp(suffix='.xml')
                    os.close(f)

                    command = (f'./{self.binary} '
                               f'--gtest_output="xml:{tmp_report}" '
                               f'--gtest_filter="{case_full}" '
                               f'{self.opts}')
                    logging.info("GTest running command: %s", command)
                    try:
                        subprocess.run(
                                args=command,
                                stderr=output_f,
                                stdout=output_f,
                                timeout=self.timeout,
                                check=True,
                                shell=True
                        )

                        tmp_xml = JUnitXML(file=tmp_report)

                        report_xml += tmp_xml

                        Path(tmp_report).unlink()
                    except subprocess.CalledProcessError as cpe:
                        self.errored_tests.append(case_full)

                        errored_cases.append(ErroredCase(case, '',
                                                         datetime.datetime\
                                                                 .now()\
                                                                 .isoformat(),
                                                         '0', cpe.stderr, ''))
                self.errored.append(ErroredSuite(suite, '', timestamp,
                                                 errored_cases))
        report_xml.write(self.report)

    def _report_skipped_tests(self) -> None:
        if self.skipped is not None:
            report_xml = JUnitXML(file=self.report)
            # Assume we didn't make up test cases, and didn't use abreviated names.
            # We may want to revisit this to remove the assumption.
            skipped_xml = JUnitXML.make_from_skipped(self.skipped.get_suites())

            report_xml += skipped_xml

            report_xml.write(self.report)

    def _report_errored_tests(self) -> None:
        if self.errored is not None:
            report_xml = JUnitXML(file=self.report)

            errored_xml = JUnitXML.make_from_errored(self.errored)

            report_xml += errored_xml

            report_xml.write(self.report)

    @classmethod
    def get_name_framework(cls) -> str:
        return 'googletest'

    _run_impl = _run_gtest
