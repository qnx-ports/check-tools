"""
Provides definitions for running googletest tests.
"""

import logging
import subprocess
from typing import List, Optional

from .test import BinaryTest
from .skipped import Skipped
from .junitxml import JUnitXML

class GTest(BinaryTest):
    """
    Defines how to run and report a googletest test.
    """
    errored_tests: List[str] = []
    skipped_tests: List[str] = []

    def __init__(self, binary: str,
                 report: str, output: str, opts: str,
                 skipped: Optional[Skipped], timeout: Optional[int] = None):
        super().__init__(binary, report, output, opts, skipped, timeout)

        # Googletest uniquely identifies tests with the pattern `<suite>.<case>`
        if self.skipped is not None:
            for suite in self.skipped.get_suites():
                self.skipped_tests += [suite.get_name() + '.' + case_name
                                       for case_name in suite.get_case_names()]

    def _run_gtest(self) -> None:
        # TODO: Need to do something special to report error exit codes as error
        #       in JUnitXML. Will need to run them individually and track
        #       errored. PyTest handles this itself...
        command = (f'./{self.binary} --gtest_output="xml:{self.report}" '
                   f'--gtest_filter="*-{':'.join(self.skipped_tests)}" '
                   f'{self.opts}')
        logging.info("GTest running command: %s", command)
        with open(self.get_output(), 'a', encoding="utf-8") as output_f:
            subprocess.run(
                    args=command,
                    stderr=output_f,
                    stdout=output_f,
                    timeout=self.timeout,
                    check=False,
                    shell=True
            )

    def _report_skipped_tests(self) -> None:
        if self.skipped is not None:
            report_xml = JUnitXML(file=self.report)
            # Assume we didn't make up test cases, and didn't use abreviated names.
            # We may want to revisit this to remove the assumption.
            skipped_xml = JUnitXML.make_from_skipped(self.skipped.get_suites())

            report_xml += skipped_xml

            report_xml.write(self.report)

    #TODO
    def _report_errored_tests(self) -> None:
        pass

    @classmethod
    def get_name_framework(cls) -> str:
        return 'googletest'

    _run_impl = _run_gtest
