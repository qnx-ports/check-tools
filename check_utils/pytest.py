"""
Provides definitions for running pytest tests.
"""

import logging
import subprocess
from typing import List

from .test import ProjectTest

class PyTest(ProjectTest):
    """
    Defines how to run and report a pytest test.
    """
    errored: List[str] = []

    def _run_pytest(self) -> None:
        command = ('pytest '
                   f'--junit-xml={self.report} '
                   f'{self.opts} {self.path}')
        if len(self.skipped) != 0:
            case_names = [case
                          for s in self.skipped for case in s.get_case_names()]
            formatted_skipped = [f'not {case}' for case in case_names]
            command += '-k "' + ' and '.join(formatted_skipped) + '" '
        logging.info("PyTest running command: %s", command)
        with open(self.get_output(), 'a', encoding="utf-8") as output_f:
            subprocess.run(
                    args=command,
                    stderr=output_f,
                    stdout=output_f,
                    timeout=self.timeout,
                    check=False,
                    shell=True
            )

    @classmethod
    def get_name_framework(cls) -> str:
        return 'pytest'

    _run_impl = _run_pytest
