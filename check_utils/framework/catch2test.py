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
Provides definitions for running catch2 tests.
"""

import logging
import os
from pathlib import Path
import subprocess
import tempfile
from typing import List

from ..junitxml import JUnitXML
from ..test import BinaryTest

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
        if len(self.meta.get_skipped()) != 0:
            command += '*,~{} ' \
                    .format(",~" \
                    .join(case_name
                          for skipped in self.meta.get_skipped()
                          for case_name in skipped.get_case_names()))

        self._info_cmd(command)
        res = subprocess.run(
                args=command,
                timeout=self.timeout,
                capture_output=True \
                        if logging.getLogger().isEnabledFor(logging.INFO) \
                        else False,
                check=False,
                shell=True,
                text=True,
        )
        self._info_result(command, res)

        report_xml = JUnitXML(tmp_report)
        Path(tmp_report).unlink()
        return report_xml

    @classmethod
    def should_report_skipped_tests(cls) -> None:
        return False

    @classmethod
    def get_name_framework(cls) -> str:
        return 'catch2'

    @classmethod
    def log_support(cls) -> None:
        cls._warn_partial_support()

    _run_impl = _run_catch2test
