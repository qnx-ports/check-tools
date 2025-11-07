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

from check_utils import Catch2Test, Skipped, JUnitXML, TestMeta
import common

MKSTEMP_REPORT_FILE: Final[str] = f'./tmp_mkstemp_{Path(__file__).stem}.xml'

def mkstemp_mock(suffix: str = None):
    tmp_xml = JUnitXML.make_from_passed([])
    tmp_xml.write(MKSTEMP_REPORT_FILE)
    return (os.open(MKSTEMP_REPORT_FILE, os.O_RDWR | os.O_CREAT), MKSTEMP_REPORT_FILE)

@patch.object(tempfile, 'mkstemp', mkstemp_mock)
@pytest.mark.parametrize('opts,timeout', [
    ('', None), ('--my-custom-opt1 --my-custom-opt2', None),
    ('', 300), ('--my-custom-opt1 --my-custom-opt2', 300)
    ])
def test__run_catch2test(mocker, opts, timeout):
    meta = TestMeta(Catch2Test)
    catch2tests = list(Catch2Test._generate_test_list('bin', opts, meta,
                                                      timeout))

    assert len(catch2tests) == 1
    catch2test = catch2tests[0]

    run_mock = mocker.patch('subprocess.run')
    run_mock.return_value = subprocess.CompletedProcess([], 0, "", "")

    expected_kwargs = {
            'args': f'./bin --reporter xml::out={MKSTEMP_REPORT_FILE} {opts} ',
            'capture_output': True,
            'timeout': timeout,
            'check': False,
            'shell': True,
            'text': True,
            }

    catch2test._run_catch2test()

    subprocess.run.assert_called_once_with(**expected_kwargs)

@patch.object(tempfile, 'mkstemp', mkstemp_mock)
def test__run_catch2test_skipped1(mocker):
    skipped = Skipped.make_from_dict({'name': 'bin1'})

    meta = TestMeta(Catch2Test, skipped=skipped.get_suites())
    catch2tests = list(Catch2Test._generate_test_list('bin1', '', meta, None))

    assert len(catch2tests) == 1
    catch2test = catch2tests[0]

    run_mock = mocker.patch('subprocess.run')
    run_mock.return_value = subprocess.CompletedProcess([], 0, "", "")

    expected_kwargs = {
            'args': f'./bin1 --reporter xml::out={MKSTEMP_REPORT_FILE}  ',
            'capture_output': True,
            'timeout': None,
            'check': False,
            'shell': True,
            'text': True,
            }

    catch2test._run_catch2test()

    subprocess.run.assert_called_once_with(**expected_kwargs)

@patch.object(tempfile, 'mkstemp', mkstemp_mock)
def test__run_catch2test_skipped2(mocker):
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

    meta = TestMeta(Catch2Test, skipped=skipped.get_suites())
    catch2tests = list(Catch2Test._generate_test_list('bin2', '', meta, None))

    assert len(catch2tests) == 1
    catch2test = catch2tests[0]

    run_mock = mocker.patch('subprocess.run')
    run_mock.return_value = subprocess.CompletedProcess([], 0, "", "")

    expected_kwargs = {
            'args': f'./bin2 --reporter xml::out={MKSTEMP_REPORT_FILE}  *,~case1,~case2,~case3 ',
            'capture_output': True,
            'timeout': None,
            'check': False,
            'shell': True,
            'text': True,
            }

    catch2test._run_catch2test()

    subprocess.run.assert_called_once_with(**expected_kwargs)

def test_should_report_skipped_tests():
    assert not Catch2Test.should_report_skipped_tests()

def test_get_name_framework():
    assert Catch2Test.get_name_framework() == 'catch2'

def test__run_impl():
    assert Catch2Test._run_impl == Catch2Test._run_catch2test
