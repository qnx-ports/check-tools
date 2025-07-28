"""
Provides definitions for running googletest tests.
"""

import datetime
import logging
import os
from pathlib import Path
import subprocess
import tempfile
from typing import Generator, List, Optional

from .test import BinaryTest, GenericTest, TestMeta
from .errored import ErroredCase, ErroredSuite
from .junitxml import JUnitXML

class GTest(BinaryTest):
    """
    Defines how to run and report a googletest test.
    """
    suite: str
    case: str
    skipped_tests: List[str]

    def __init__(self, binary: str, suite: str, case: str, output: str,
                 opts: str, meta: TestMeta, timeout: Optional[int] = None):
        super().__init__(binary, output, opts, meta, timeout)

        self.suite = suite
        self.case = case

    @classmethod
    def _generate_test_list(cls, binary: str, output: str,
                            opts: str, meta: TestMeta,
                            timeout: Optional[int] = None) -> Generator[
                                    GenericTest, None, None]:
        # Googletest uniquely identifies tests with the pattern `<suite>.<case>`
        skipped_tests = []
        for suite in meta.get_skipped():
            skipped_tests += [suite.get_name() + '.' + case_name
                              for case_name in suite.get_case_names()]

        # Run test cases individually so we can catch an error.
        #
        # FIXME: Do this in a more reliable way. EXIT_FAILURE can occur without
        # a bad output from --gtest_list_tests.
        command = f'./{binary} --gtest_list_tests'
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
        for line in output.splitlines():
            # Can include comments for GetParam()
            ind = line.find('#')
            if ind != -1:
                line = line[:ind]
            stripped = line.strip()
            if ' ' not in stripped and stripped.endswith('.'):
                # Suite identifier.
                #
                # Update suite.
                suite = stripped[:-1]
            elif len(suite) != 0 and line.startswith(' '):
                # Case identifier.
                case = stripped
                case_full = suite + '.' + case

                if case_full not in skipped_tests:
                    yield cls(binary, suite, case, output, opts, meta, timeout)

    def _run_gtest(self) -> None:
        report_xml: Optional[JUnitXML] = None
        # Suite timestamp
        timestamp = datetime.datetime.now().isoformat()

        case_full = self.suite + '.' + self.case

        f, tmp_report = tempfile.mkstemp(suffix='.xml')
        os.close(f)

        # Googletest uses a premature-exit-file to allow runner
        # programs to detect premature exits. See:
        # https://google.github.io/googletest/advanced.html
        # We use this to detect errored cases.
        f, tmp_premature_exit = tempfile.mkstemp()
        os.close(f)
        env = os.environ.copy()
        env['TEST_PREMATURE_EXIT_FILE'] = tmp_premature_exit

        # subprocess.run does not support io.StringIO stderr
        stderr_f, tmp_stderr = tempfile.mkstemp()

        command = (f'./{self.binary} '
                   f'--gtest_output="xml:{tmp_report}" '
                   f'--gtest_filter="{case_full}" '
                   f'{self.opts}')
        logging.info("GTest running command: %s", command)
        with open('/dev/null', 'w') as output_f:
            subprocess.run(
                    args=command,
                    stdout=output_f,
                    stderr=stderr_f,
                    timeout=self.timeout,
                    check=False,
                    shell=True,
                    env=env
            )
        os.close(stderr_f)
        if Path(tmp_premature_exit).exists():
            stderr = ''
            with open(tmp_stderr, 'r', encoding="utf-8") as f:
                stderr = f.read()
            logging.info('%s terminated with err %s.', self.binary,
                         stderr)

            report_xml = JUnitXML\
                    .make_from_errored([ErroredSuite(self.suite,
                                                     '',
                                                     timestamp,
                                                     [ErroredCase(self.case,
                                                                  '',
                                                                  datetime.datetime\
                                                                          .now()\
                                                                          .isoformat(),
                                                                  '0',
                                                                  stderr,
                                                                  '')])])

            Path(tmp_premature_exit).unlink()
            Path(tmp_report).unlink(missing_ok=True)
        else:
            report_xml = JUnitXML(file=tmp_report)

            Path(tmp_report).unlink()

        Path(tmp_stderr).unlink()

        return report_xml

    @classmethod
    def should_report_skipped_tests(cls) -> None:
        return True

    @classmethod
    def get_name_framework(cls) -> str:
        return 'googletest'

    _run_impl = _run_gtest
