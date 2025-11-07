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
        if len(self.meta.get_skipped()) != 0:
            command += '-skipblacklisted '
            with Path(self.binary).parent.joinpath('BLACKLIST').open('a') as f:
                for skipped in self.meta.get_skipped():
                    for case_name in skipped.get_case_names():
                        f.write(f'\n[{case_name}]\nqnx\n')

        self._info_cmd(command)
        res = subprocess.run(
                args=command,
                capture_output=True \
                        if logging.getLogger().isEnabledFor(logging.INFO) \
                        else False,
                timeout=self.timeout,
                check=False,
                shell=True,
                text=True,
        )
        self._info_result(command, res)

        report_obj = JUnitXML(file=tmp_report)
        Path(tmp_report).unlink()
        return report_obj

    @classmethod
    def should_report_skipped_tests(cls) -> None:
        return False

    @classmethod
    def get_name_framework(cls) -> str:
        return 'qt-test'

    @classmethod
    def log_support(cls) -> None:
        cls._warn_partial_support()

    _run_impl = _run_qttest
