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
Unit tests for gtest.py
"""

import os
from pathlib import Path
import pytest
import subprocess
import tempfile
from typing import Final
from unittest.mock import ANY, patch

from check_utils import GTest, Skipped, JUnitXML, TestMeta
import common

MKSTEMP_REPORT_FILE: Final[str] = f'./tmp_mkstemp_{Path(__file__).stem}.xml'
PREMATURE_EXIT_FILE: Final[str] = f'./tmp_mkstemp_{Path(__file__).stem}_exit'

class MkstempMockWrapper:
    count = 0

    @classmethod
    def mkstemp_mock(cls, suffix: str = None):
        # Spoof a test run...
        # It first creates a temporary xml file, then creates a file to track
        # premature exits.
        if cls.count == 0:
            cls.count = 1
            tmp_xml = JUnitXML.make_from_passed([])
            tmp_xml.write(MKSTEMP_REPORT_FILE)
            return (os.open(MKSTEMP_REPORT_FILE, os.O_RDWR | os.O_CREAT), MKSTEMP_REPORT_FILE)
        else:
            cls.count = 0
            return (os.open(PREMATURE_EXIT_FILE, os.O_RDWR | os.O_CREAT), PREMATURE_EXIT_FILE)

@patch.object(tempfile, 'mkstemp', MkstempMockWrapper.mkstemp_mock)
@pytest.mark.parametrize('opts,timeout,blurb', [
    ('', None, ''),
    ('--my-custom-opt1 --my-custom-opt2', 300, 'Run this program with --check_for_leaks to enable custom leak checking in the tests.\n'),
    ('-a', 1800, 'Running main() from googletest/googletest/src/gtest_main.cc\n')
    ])
def test__run_gtest(mocker, opts, timeout, blurb):
    getstatusoutput_mock = mocker.patch('subprocess.getstatusoutput')
    getstatusoutput_mock.return_value = (0,
                                         blurb +
                                         'Foo.\n'
                                         ' Test1\n'
                                         ' Test2\n'
                                         'Bar.\n'
                                         ' 3tseT\n'
                                         ' Ttse4')

    meta = TestMeta(GTest)
    gtest_tests = list(GTest._generate_test_list('bin', opts, meta, timeout))

    assert len(gtest_tests) == 4

    run_mock = mocker.patch('subprocess.run')
    run_mock.return_value = subprocess.CompletedProcess([], 0, "".encode(), "".encode())

    expected_kwargs1 = {
            'args': f'./bin --gtest_output="xml:{MKSTEMP_REPORT_FILE}" --gtest_filter="Foo.Test1" {opts}',
            'capture_output': True,
            'timeout': timeout,
            'check': False,
            'shell': True,
            'env': ANY,
            }

    expected_kwargs2 = {
            'args': f'./bin --gtest_output="xml:{MKSTEMP_REPORT_FILE}" --gtest_filter="Foo.Test2" {opts}',
            'capture_output': True,
            'timeout': timeout,
            'check': False,
            'shell': True,
            'env': ANY,
            }

    expected_kwargs3 = {
            'args': f'./bin --gtest_output="xml:{MKSTEMP_REPORT_FILE}" --gtest_filter="Bar.3tseT" {opts}',
            'capture_output': True,
            'timeout': timeout,
            'check': False,
            'shell': True,
            'env': ANY,
            }

    expected_kwargs4 = {
            'args': f'./bin --gtest_output="xml:{MKSTEMP_REPORT_FILE}" --gtest_filter="Bar.Ttse4" {opts}',
            'capture_output': True,
            'timeout': timeout,
            'check': False,
            'shell': True,
            'env': ANY,
            }

    for gtest in gtest_tests:
        gtest._run_gtest()

    subprocess.run.assert_any_call(**expected_kwargs1)
    subprocess.run.assert_any_call(**expected_kwargs2)
    subprocess.run.assert_any_call(**expected_kwargs3)
    subprocess.run.assert_any_call(**expected_kwargs4)

    assert not Path(MKSTEMP_REPORT_FILE).exists()
    assert not Path(PREMATURE_EXIT_FILE).exists()

@patch.object(tempfile, 'mkstemp', MkstempMockWrapper.mkstemp_mock)
def test__run_gtest_skipped1(mocker):
    getstatusoutput_mock = mocker.patch('subprocess.getstatusoutput')
    getstatusoutput_mock.return_value = (0,
                                         'Foo.\n'
                                         ' Test1\n'
                                         ' Test2\n'
                                         'Bar.\n'
                                         ' 3tseT\n'
                                         ' Ttse4')

    skipped = Skipped.make_from_dict({'name': 'bin1'})

    meta = TestMeta(GTest, skipped=skipped.get_suites())
    gtest_tests = list(GTest._generate_test_list('bin1', '', meta, None))

    assert len(gtest_tests) == 4

    run_mock = mocker.patch('subprocess.run')
    run_mock.return_value = subprocess.CompletedProcess([], 0, "".encode(), "".encode())

    expected_kwargs1 = {
            'args': f'./bin1 --gtest_output="xml:{MKSTEMP_REPORT_FILE}" --gtest_filter="Foo.Test1" ',
            'capture_output': True,
            'timeout': None,
            'check': False,
            'shell': True,
            'env': ANY,
            }

    expected_kwargs2 = {
            'args': f'./bin1 --gtest_output="xml:{MKSTEMP_REPORT_FILE}" --gtest_filter="Foo.Test2" ',
            'capture_output': True,
            'timeout': None,
            'check': False,
            'shell': True,
            'env': ANY,
            }

    expected_kwargs3 = {
            'args': f'./bin1 --gtest_output="xml:{MKSTEMP_REPORT_FILE}" --gtest_filter="Bar.3tseT" ',
            'capture_output': True,
            'timeout': None,
            'check': False,
            'shell': True,
            'env': ANY,
            }

    expected_kwargs4 = {
            'args': f'./bin1 --gtest_output="xml:{MKSTEMP_REPORT_FILE}" --gtest_filter="Bar.Ttse4" ',
            'capture_output': True,
            'timeout': None,
            'check': False,
            'shell': True,
            'env': ANY,
            }

    for gtest in gtest_tests:
        gtest._run_gtest()

    subprocess.run.assert_any_call(**expected_kwargs1)
    subprocess.run.assert_any_call(**expected_kwargs2)
    subprocess.run.assert_any_call(**expected_kwargs3)
    subprocess.run.assert_any_call(**expected_kwargs4)

    assert not Path(MKSTEMP_REPORT_FILE).exists()
    assert not Path(PREMATURE_EXIT_FILE).exists()

@patch.object(tempfile, 'mkstemp', MkstempMockWrapper.mkstemp_mock)
def test__run_gtest_skipped2(mocker):
    getstatusoutput_mock = mocker.patch('subprocess.getstatusoutput')
    getstatusoutput_mock.return_value = (0,
                                         'Foo.\n'
                                         ' Test1\n'
                                         ' Test2\n'
                                         'Bar.\n'
                                         ' 3tseT\n'
                                         ' Ttse4')

    skipped = Skipped.make_from_dict({
        'name': 'bin2',
        'norun': False,
        'suites': [
            {
                'name': 'Foo',
                'file': 'file1',
                'timestamp': '1970-01-01T00:00:00+00:00',
                'cases': [
                        {
                            'name': 'Test1',
                            'line': '1',
                            'os': ['8.0.0'],
                        },
                        {
                            'name': 'Test2',
                            'line': '2'
                        }]},
            {
                'name': 'Bar',
                'file': 'file2',
                'timestamp': '2000-01-01T00:00:00+00:00',
                'cases': [
                        {
                            'name': '3tseT',
                            'line': '1',
                            'os': ['7.1.0'],
                            'platform': ['qemu'],
                            'arch': ['x86_64']
                        }]}]})


    meta = TestMeta(GTest, skipped=skipped.get_suites())
    gtest_tests = list(GTest._generate_test_list('bin2', '', meta, None))

    assert len(gtest_tests) == 1

    run_mock = mocker.patch('subprocess.run')
    run_mock.return_value = subprocess.CompletedProcess([], 0, "".encode(), "".encode())

    expected_kwargs = {
            'args': f'./bin2 --gtest_output="xml:{MKSTEMP_REPORT_FILE}" --gtest_filter="Bar.Ttse4" ',
            'capture_output': True,
            'timeout': None,
            'check': False,
            'shell': True,
            'env': ANY,
            }

    for gtest in gtest_tests:
        gtest._run_gtest()

    subprocess.run.assert_called_once_with(**expected_kwargs)

    assert not Path(MKSTEMP_REPORT_FILE).exists()
    assert not Path(PREMATURE_EXIT_FILE).exists()

@patch.object(tempfile, 'mkstemp', MkstempMockWrapper.mkstemp_mock)
def test__run_gtest_errored1(mocker):
    getstatusoutput_mock = mocker.patch('subprocess.getstatusoutput')
    getstatusoutput_mock.return_value = (0,
                                         'Foo.\n'
                                         ' Test1\n'
                                         ' Test2\n'
                                         'Bar.\n'
                                         ' 3tseT\n'
                                         ' Ttse4')

    meta = TestMeta(GTest)
    gtest_tests = list(GTest._generate_test_list('bin1', '', meta, None))

    assert len(gtest_tests) == 4

    run_mock = mocker.patch('subprocess.run')
    run_mock.return_value = subprocess.CompletedProcess([], 0, "".encode(), "".encode())

    expected_kwargs1 = {
            'args': f'./bin1 --gtest_output="xml:{MKSTEMP_REPORT_FILE}" --gtest_filter="Foo.Test1" ',
            'capture_output': True,
            'timeout': None,
            'check': False,
            'shell': True,
            'env': ANY,
            }

    expected_kwargs2 = {
            'args': f'./bin1 --gtest_output="xml:{MKSTEMP_REPORT_FILE}" --gtest_filter="Foo.Test2" ',
            'capture_output': True,
            'timeout': None,
            'check': False,
            'shell': True,
            'env': ANY,
            }

    expected_kwargs3 = {
            'args': f'./bin1 --gtest_output="xml:{MKSTEMP_REPORT_FILE}" --gtest_filter="Bar.3tseT" ',
            'capture_output': True,
            'timeout': None,
            'check': False,
            'shell': True,
            'env': ANY,
            }

    expected_kwargs4 = {
            'args': f'./bin1 --gtest_output="xml:{MKSTEMP_REPORT_FILE}" --gtest_filter="Bar.Ttse4" ',
            'capture_output': True,
            'timeout': None,
            'check': False,
            'shell': True,
            'env': ANY,
            }

    errored_obj = JUnitXML.make_from_passed([])
    for gtest in gtest_tests:
        errored_obj += gtest._run_gtest()

    subprocess.run.assert_any_call(**expected_kwargs1)
    subprocess.run.assert_any_call(**expected_kwargs2)
    subprocess.run.assert_any_call(**expected_kwargs3)
    subprocess.run.assert_any_call(**expected_kwargs4)

    assert not errored_obj.is_success() # At least one test case failed.

    assert not Path(MKSTEMP_REPORT_FILE).exists()
    assert not Path(PREMATURE_EXIT_FILE).exists()

def test_should_report_skipped_tests():
    assert GTest.should_report_skipped_tests()

def test_get_name_framework():
    assert GTest.get_name_framework() == 'googletest'

def test__run_impl():
    assert GTest._run_impl == GTest._run_gtest
