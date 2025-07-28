"""
Provides definitions for running catch2 tests.
"""

import logging
import os
from pathlib import Path
import subprocess
import tempfile
from typing import List

from .junitxml import JUnitXML
from .test import BinaryTest

class Catch2Test(BinaryTest):
    """
    Defines how to run and report a catch2 test.
    """
    errored: List[str] = []

    def _run_catch2test(self) -> None:
        f, tmp_report = tempfile.mkstemp(suffix='.xml')
        os.close(f)

        command = (f'./{self.binary} '
                   f'--reporter xml::out={tmp_report} '
                   f'{self.opts} ')
        if self.skipped is not None and not self.skipped.is_empty():
            command += f'*,~{",~".join(self.skipped.get_case_names())} '

        logging.info("Catch2Test running command: %s", command)
        with open('/dev/null', 'w') as output_f:
            subprocess.run(
                    args=command,
                    stderr=output_f,
                    stdout=output_f,
                    timeout=self.timeout,
                    check=False,
                    shell=True
            )

        report_xml = JUnitXML(tmp_report)
        Path(tmp_report).unlink()
        return report_xml

    @classmethod
    def should_report_skipped_tests(cls) -> None:
        return False

    @classmethod
    def get_name_framework(cls) -> str:
        return 'catch2'

    _run_impl = _run_catch2test
