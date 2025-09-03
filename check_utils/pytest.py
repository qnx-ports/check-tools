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
Provides definitions for running pytest tests.
"""

import logging
import os
from pathlib import Path
import subprocess
import tempfile
from typing import List

from .junitxml import JUnitXML
from .test import ProjectTest

class PyTest(ProjectTest):
    """
    Defines how to run and report a pytest test.
    """
    errored: List[str] = []

    def _run_pytest(self) -> None:
        f, tmp_report = tempfile.mkstemp(suffix='.xml')
        os.close(f)

        command = ('pytest '
                   f'--junitxml={tmp_report} '
                   f'-o junit_family=xunit1 '
                   f'-n {self.num_jobs} '
                   f'{self.opts} {self.path} ')
        if len(self.meta.get_skipped()) != 0:
            case_names = [case
                          for s in self.meta.get_skipped()
                          for case in s.get_case_names()]
            formatted_skipped = [f'not {case}' for case in case_names]
            command += '-k "' + ' and '.join(formatted_skipped) + '" '
        logging.info("%s running command: %s", PyTest.__name__, command)
        with open('/dev/null', 'w') as output_f:
            subprocess.run(
                    args=command,
                    stderr=output_f,
                    stdout=output_f,
                    timeout=self.timeout,
                    check=False,
                    shell=True
            )

        report_xml = JUnitXML(file=tmp_report)
        Path(tmp_report).unlink()
        return report_xml

    @classmethod
    def should_report_skipped_tests(cls) -> None:
        return True

    @classmethod
    def get_name_framework(cls) -> str:
        return 'pytest'

    @classmethod
    def log_support(cls) -> None:
        cls._warn_partial_support()

    _run_impl = _run_pytest
