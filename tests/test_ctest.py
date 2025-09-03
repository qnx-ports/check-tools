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
Unit tests for ctest.py
"""

import os
from pathlib import Path
import pytest
import subprocess
import tempfile
from typing import Final
from unittest.mock import ANY, patch

from check_utils import CTest, SkippedSuite, JUnitXML, TestMeta
import common

MKSTEMP_REPORT_FILE: Final[str] = f'./tmp_mkstemp_{Path(__file__).stem}.xml'
OUTPUT_FILE: Final[str] = f'./tmp_{Path(__file__).stem}.txt'

@pytest.fixture()
def output_file():
    output_path = Path(OUTPUT_FILE)

    # Setup
    if (output_path.exists()):
        output_path.unlink()

    yield OUTPUT_FILE

    # Teardown
    if (output_path.exists()):
        output_path.unlink()

def mkstemp_mock(suffix: str = None):
    tmp_xml = JUnitXML.make_from_passed([])
    tmp_xml.write(MKSTEMP_REPORT_FILE)
    return (os.open(MKSTEMP_REPORT_FILE, os.O_RDWR | os.O_CREAT), MKSTEMP_REPORT_FILE)

@patch.object(tempfile, 'mkstemp', mkstemp_mock)
@pytest.mark.parametrize('opts,timeout,num_jobs', [
    ('', None, 1), ('--my-custom-opt1 --my-custom-opt2', None, 2),
    ('', 300, 3), ('--my-custom-opt1 --my-custom-opt2', 300, 4)
    ])
def test__run_ctest(mocker, output_file, opts, timeout, num_jobs):
    meta = TestMeta(CTest)
    path = ''
    p = str(Path(path).absolute())
    ctest = CTest(path, output_file, opts, meta, timeout)
    ctest.set_num_jobs(num_jobs)

    mocker.patch('subprocess.run')

    expected_kwargs = {
            'args': f'ctest --output-junit={MKSTEMP_REPORT_FILE} -j {num_jobs} {opts} --build-dir {p} ',
            'stderr': ANY,
            'stdout': ANY,
            'timeout': timeout,
            'check': False,
            'shell': True
            }

    ctest._run_ctest()

    subprocess.run.assert_called_once_with(**expected_kwargs)

@patch.object(tempfile, 'mkstemp', mkstemp_mock)
def test__run_ctest_skipped(mocker, output_file):
    # In reality ctest generates junit with a single suite of name '(empty)'
    skip_list = [
            SkippedSuite.make_from_dict(
                {
                    'name': 'suite1',
                    'file': 'file1',
                    'timestamp': '1970-01-01T00:00:00+00:00',
                    'cases': [
                            {
                                'name': 'test_foo1',
                                'line': '1',
                                'os': ['8.0.0'],
                            },
                            {
                                'name': 'test_foo2',
                                'line': '2'
                            }]}),
            SkippedSuite.make_from_dict(
                {
                    'name': 'suite2',
                    'file': 'file2',
                    'timestamp': '2000-01-01T00:00:00+00:00',
                    'cases': [
                            {
                                'name': 'test_foo3',
                                'line': '1',
                                'os': ['7.1.0'],
                                'arch': ['x86_64']
                            }]})
            ]
    meta = TestMeta(CTest, skipped=skip_list)
    path = ''
    p = str(Path(path).absolute())
    opts = ''
    ctest = CTest(path, output_file, opts, meta, None)

    mocker.patch('subprocess.run')

    expected_kwargs = {
            'args': f'ctest --output-junit={MKSTEMP_REPORT_FILE} -j 1 {opts} --build-dir {p} --exclude-regex "(test_foo1|test_foo2|test_foo3)" ',
            'stderr': ANY,
            'stdout': ANY,
            'timeout': None,
            'check': False,
            'shell': True
            }

    ctest._run_ctest()

    subprocess.run.assert_called_once_with(**expected_kwargs)

def test_should_report_skipped_tests():
    assert not CTest.should_report_skipped_tests()

def test_get_name_framework():
    assert CTest.get_name_framework() == 'ctest'

def test__run_impl():
    assert CTest._run_impl == CTest._run_ctest
