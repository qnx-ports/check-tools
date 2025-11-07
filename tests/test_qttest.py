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
Unit tests for catch2test.py
"""

import os
from pathlib import Path
import pytest
import subprocess
import tempfile
from typing import Final
from unittest.mock import ANY, patch

from check_utils import QtTest, Skipped, JUnitXML, TestMeta
import common

MKSTEMP_REPORT_FILE: Final[str] = f'./tmp_mkstemp_{Path(__file__).stem}.xml'
BLACKLIST_FILE: Final[str] = './BLACKLIST'

@pytest.fixture()
def blacklist_file():
    blacklist_path = Path(BLACKLIST_FILE)

    # Setup
    if (blacklist_path.exists()):
        blacklist_path.unlink()

    yield BLACKLIST_FILE

    # Teardown
    if (blacklist_path.exists()):
        blacklist_path.unlink()

def mkstemp_mock(suffix: str = None):
    tmp_xml = JUnitXML.make_from_passed([])
    tmp_xml.write(MKSTEMP_REPORT_FILE)
    return (os.open(MKSTEMP_REPORT_FILE, os.O_RDWR | os.O_CREAT), MKSTEMP_REPORT_FILE)

@patch.object(tempfile, 'mkstemp', mkstemp_mock)
@pytest.mark.parametrize('opts,timeout', [
    ('', None), ('--my-custom-opt1 --my-custom-opt2', None),
    ('', 300), ('--my-custom-opt1 --my-custom-opt2', 300)
    ])
def test__run_qttest(mocker, opts, timeout):
    meta = TestMeta(QtTest)
    qttests = list(QtTest._generate_test_list('bin', opts, meta,
                                              timeout))

    assert len(qttests) == 1
    qttest = qttests[0]

    run_mock = mocker.patch('subprocess.run')
    run_mock.return_value = subprocess.CompletedProcess([], 0, "", "")

    expected_kwargs = {
            'args': f'./bin -o {MKSTEMP_REPORT_FILE},junitxml {opts} ',
            'capture_output': True,
            'timeout': timeout,
            'check': False,
            'shell': True,
            'text': True,
            }

    qttest._run_qttest()

    subprocess.run.assert_called_once_with(**expected_kwargs)

    assert not Path(BLACKLIST_FILE).exists()

@patch.object(tempfile, 'mkstemp', mkstemp_mock)
def test__run_qttest_skipped1(mocker):
    skipped = Skipped.make_from_dict({'name': 'bin1'})
    meta = TestMeta(QtTest, skipped=skipped.get_suites())
    qttests = list(QtTest._generate_test_list('bin1', '', meta,
                                              None))

    assert len(qttests) == 1
    qttest = qttests[0]

    run_mock = mocker.patch('subprocess.run')
    run_mock.return_value = subprocess.CompletedProcess([], 0, "", "")

    expected_kwargs = {
            'args': f'./bin1 -o {MKSTEMP_REPORT_FILE},junitxml  ',
            'capture_output': True,
            'timeout': None,
            'check': False,
            'shell': True,
            'text': True,
            }

    qttest._run_qttest()

    subprocess.run.assert_called_once_with(**expected_kwargs)

    assert not Path(BLACKLIST_FILE).exists()

@patch.object(tempfile, 'mkstemp', mkstemp_mock)
def test__run_qttest_skipped2(mocker, blacklist_file):
    skipped = Skipped.make_from_dict({
        'name': 'bin2',
        'norun': False,
        'suites': [
            {
                'name': 'suite1',
                'file': 'file1',
                'timestamp': '1970-01-01T00:00:00+00:00',
                'cases': [
                        {
                            'name': 'case1',
                            'line': '1',
                            'os': ['8.0.0'],
                        },
                        {
                            'name': 'case2',
                            'line': '2'
                        }]},
            {
                'name': 'suite2',
                'file': 'file2',
                'timestamp': '2000-01-01T00:00:00+00:00',
                'cases': [
                        {
                            'name': 'case3',
                            'line': '1',
                            'os': ['7.1.0'],
                            'platform': ['qemu'],
                            'arch': ['x86_64']
                        }]}]})
    meta = TestMeta(QtTest, skipped=skipped.get_suites())
    qttests = list(QtTest._generate_test_list('bin2', '', meta,
                                              None))

    assert len(qttests) == 1
    qttest = qttests[0]

    run_mock = mocker.patch('subprocess.run')
    run_mock.return_value = subprocess.CompletedProcess([], 0, "", "")

    expected_kwargs = {
            'args': f'./bin2 -o {MKSTEMP_REPORT_FILE},junitxml  -skipblacklisted ',
            'capture_output': True,
            'timeout': None,
            'check': False,
            'shell': True,
            'text': True,
            }

    qttest._run_qttest()

    subprocess.run.assert_called_once_with(**expected_kwargs)

    assert Path(BLACKLIST_FILE).exists()

    # Check the fields...
    blacklist = ''
    with Path(BLACKLIST_FILE).open('r') as f:
        blacklist = f.read()
    assert blacklist == ('\n'
                         '[case1]\n'
                         'qnx\n'
                         '\n'
                         '[case2]\n'
                         'qnx\n'
                         '\n'
                         '[case3]\n'
                         'qnx\n')

def test_should_report_skipped_tests():
    assert not QtTest.should_report_skipped_tests()

def test_get_name_framework():
    assert QtTest.get_name_framework() == 'qt-test'

def test__run_impl():
    assert QtTest._run_impl == QtTest._run_qttest
