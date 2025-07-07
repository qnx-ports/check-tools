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
        # 
        # FIXME: Do this in a more reliable way. EXIT_FAILURE can occur without
        # a bad output from --gtest_list_tests.
        command = f'./{self.binary} --gtest_list_tests'
        logging.info('GTest running command: %s', command)
        status = None
        output = None
        status, output = subprocess.getstatusoutput(command)
        if status:
            logging.error('Non-zero exit status %d '
                              'returned from %s', status,
                              command)
            raise subprocess.CalledProcessError('googletest command failed.',
                                                cmd=command)

        suite = ''
        cases = []
        self.tests = []
        for line in output.splitlines():
            # Can include comments for GetParam()
            ind = line.find('#')
            if ind != -1:
                line = line[:ind]
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

        self.errored = []
        self.errored_tests = []

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

                    # Googletest uses a premature-exit-file to allow runner
                    # programs to detect premature exits. See:
                    # https://google.github.io/googletest/advanced.html
                    # We use this to detect errored cases.
                    f, tmp_premature_exit = tempfile.mkstemp()
                    os.close(f)
                    os.environ['TEST_PREMATURE_EXIT_FILE'] = tmp_premature_exit

                    # subprocess.run does not support io.StringIO stderr
                    stderr_f, tmp_stderr = tempfile.mkstemp()

                    command = (f'./{self.binary} '
                               f'--gtest_output="xml:{tmp_report}" '
                               f'--gtest_filter="{case_full}" '
                               f'{self.opts}')
                    logging.info("GTest running command: %s", command)
                    subprocess.run(
                            args=command,
                            stdout=output_f,
                            stderr=stderr_f,
                            timeout=self.timeout,
                            check=False,
                            shell=True
                    )
                    os.close(stderr_f)
                    if Path(tmp_premature_exit).exists():
                        stderr = ''
                        with open(tmp_stderr, 'r', encoding="utf-8") as f:
                            stderr = f.read()
                        logging.info('%s terminated with err %s.', self.binary,
                                     stderr)
                        self.errored_tests.append(case_full)

                        errored_cases.append(ErroredCase(case, '',
                                                         datetime.datetime\
                                                                 .now()\
                                                                 .isoformat(),
                                                         '0',
                                                         stderr,
                                                         ''))

                        Path(tmp_premature_exit).unlink()
                        if Path(tmp_report).exists():
                            Path(tmp_report).unlink()
                    else:
                        tmp_xml = JUnitXML(file=tmp_report)

                        report_xml += tmp_xml

                        Path(tmp_report).unlink()

                    Path(tmp_stderr).unlink()

                if len(errored_cases) != 0:
                    self.errored.append(ErroredSuite(suite, '', timestamp,
                                                     errored_cases))
        report_xml.write(self.report)

        os.environ['TEST_PREMATURE_EXIT_FILE'] = ''

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
