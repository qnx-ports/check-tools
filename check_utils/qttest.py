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

class QtTest(BinaryTest):
    """
    Defines how to run and report a qt test.
    """
    errored: List[str] = []

    def _run_qttest(self) -> None:
        f, tmp_report = tempfile.mkstemp(suffix='.xml')
        os.close(f)

        # Qt-test skips based on the contents of a BLACKLIST file.
        command = (f'./{self.binary} '
                   f'-o {tmp_report},junitxml '
                   f'{self.opts} ')
        if self.skipped is not None and not self.skipped.is_empty():
            command += '-skipblacklisted '
            with Path(self.binary).parent.joinpath('BLACKLIST').open('a') as f:
                for case_name in self.skipped.get_case_names():
                    f.write(f'\n[{case_name}]\nqnx\n')

        logging.info("QtTest running command: %s", command)
        with open('/dev/null', 'w') as output_f:
            subprocess.run(
                    args=command,
                    stderr=output_f,
                    stdout=output_f,
                    timeout=self.timeout,
                    check=False,
                    shell=True
            )

        report_obj = JUnitXML(file=tmp_report)
        Path(tmp_report).unlink()
        return report_obj

    @classmethod
    def should_report_skipped_tests(cls) -> None:
        return False

    @classmethod
    def get_name_framework(cls) -> str:
        return 'qt-test'

    _run_impl = _run_qttest
