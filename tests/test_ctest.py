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
Unit tests for parse_ctest.sh
"""

import copy
import os
import pytest
import subprocess

from check_utils import CheckExit, JUnitXML
import common

@pytest.mark.parametrize('flag,num', [
    ('pass', '001'),
    ('pass', '002'),
    ])
def test_parse_automake_success(flag, num):
    env = copy.copy(os.environ)
    env['START_DIR'] = f'{common.TEST_DIR}/data'

    status = 0
    try:
        subprocess.run([f'cat {common.TEST_DIR}/data/ctest_{flag}_{num}.txt | parse_ctest.sh'],
                       check=True,
                       shell=True,
                       env=env)
    except subprocess.CalledProcessError as cpe:
        status = cpe.returncode

    assert status == CheckExit.EXIT_SUCCESS
    assert JUnitXML(file=f'{common.TEST_DIR}/data/test-out/foo.xml').is_success()

@pytest.mark.parametrize('flag,num', [
    ('fail', '001'),
    ('fail', '002'),
    ])
def test_parse_automake_failure(flag, num):
    env = copy.copy(os.environ)
    env['START_DIR'] = f'{common.TEST_DIR}/data'

    status = 0
    try:
        subprocess.run([f'cat {common.TEST_DIR}/data/ctest_{flag}_{num}.txt | parse_ctest.sh'],
                       check=True,
                       shell=True,
                       env=env)
    except subprocess.CalledProcessError as cpe:
        status = cpe.returncode

    assert status == CheckExit.EXIT_FAILURE
    assert not JUnitXML(file=f'{common.TEST_DIR}/data/test-out/foo.xml').is_success()
