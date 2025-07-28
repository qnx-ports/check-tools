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
Unit tests for pytest.py
"""

import os
from pathlib import Path
import pytest
import subprocess
import tempfile
from typing import Final
from unittest.mock import ANY, patch

from check_utils import PyTest, SkippedSuite, JUnitXML, TestMeta
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
def test__run_pytest(mocker, output_file, opts, timeout, num_jobs):
    meta = TestMeta(PyTest)
    pytest = PyTest(output_file, opts, meta, timeout)
    pytest.set_num_jobs(num_jobs)

    mocker.patch('subprocess.run')

    expected_kwargs = {
            'args': f'pytest --junit-xml={MKSTEMP_REPORT_FILE} -n {num_jobs} {opts} ',
            'stderr': ANY,
            'stdout': ANY,
            'timeout': timeout,
            'check': False,
            'shell': True
            }

    pytest._run_pytest()

    subprocess.run.assert_called_once_with(**expected_kwargs)

@patch.object(tempfile, 'mkstemp', mkstemp_mock)
def test__run_mesontest_skipped(mocker, output_file):
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
    meta = TestMeta(PyTest, skipped=skip_list)
    pytest = PyTest(output_file, '', meta, None)

    mocker.patch('subprocess.run')

    expected_kwargs = {
            'args': f'pytest --junit-xml={MKSTEMP_REPORT_FILE} -n 1  -k "not test_foo1 and not test_foo2 and not test_foo3" ',
            'stderr': ANY,
            'stdout': ANY,
            'timeout': None,
            'check': False,
            'shell': True
            }

    pytest._run_pytest()

    subprocess.run.assert_called_once_with(**expected_kwargs)

def test_should_report_skipped_tests():
    assert not PyTest.should_report_skipped_tests()

def test_get_name_framework():
    assert PyTest.get_name_framework() == 'pytest'

def test__run_impl():
    assert PyTest._run_impl == PyTest._run_pytest
