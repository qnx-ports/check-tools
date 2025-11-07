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
Provides definitions for running ctest tests.
"""

import logging
import os
from pathlib import Path
import subprocess
import tempfile

from ..junitxml import JUnitXML
from ..test import ProjectTest

class CTest(ProjectTest):
    """
    Defines how to run and report a ctest test.
    """
    def _run_ctest(self) -> None:
        f, tmp_report = tempfile.mkstemp(suffix='.xml')
        os.close(f)

        p = str(Path(self.path).absolute())
        command = ('ctest '
                   f'--output-junit {tmp_report} '
                   f'-j {self.num_jobs} '
                   f'{self.opts} ')
        if len(self.meta.get_skipped()) != 0:
            case_names = [case
                          for s in self.meta.get_skipped()
                          for case in s.get_case_names()]
            command += '--exclude-regex "(' + '|'.join(case_names) + ')" '
        self._info_cmd(command)
        res = subprocess.run(
                args=command,
                timeout=self.timeout,
                capture_output=True \
                        if logging.getLogger().isEnabledFor(logging.INFO) \
                        else False,
                check=False,
                shell=True,
                cwd=p,
                text=True,
        )
        self._info_result(command, res)

        report_xml = JUnitXML(file=tmp_report)
        Path(tmp_report).unlink()
        return report_xml

    @classmethod
    def should_report_skipped_tests(cls) -> None:
        return True

    @classmethod
    def get_name_framework(cls) -> str:
        return 'ctest'

    @classmethod
    def log_support(cls) -> None:
        cls._warn_partial_support()
        logging.warning('%s requires a cmake version >=3.21.', cls.__name__)

    _run_impl = _run_ctest
