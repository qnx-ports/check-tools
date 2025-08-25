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
Unit tests for mesontest.py
"""

from pathlib import Path
import pytest
import subprocess
from typing import Final
from unittest.mock import ANY

from check_utils import MesonTest, SkippedSuite, BUILD_DIR, TestMeta, JUnitXML
import common

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

@pytest.fixture()
def xml_test_log_file():
    xml_test_log_path = BUILD_DIR.joinpath(MesonTest.XML_TEST_LOG)
    xml_test_log_path.parent.mkdir(parents=True, exist_ok=True)

    # Setup
    if (xml_test_log_path.exists()):
        xml_test_log_path.unlink()

    yield str(xml_test_log_path)

    # Teardown
    if (xml_test_log_path.exists()):
        xml_test_log_path.unlink()

@pytest.mark.parametrize('opts,timeout,num_jobs', [
    ('', None, 1), ('--my-custom-opt1 --my-custom-opt2', None, 2),
    ('', 300, 3), ('--my-custom-opt1 --my-custom-opt2', 300, 4)
    ])
def test__run_mesontest(mocker, output_file, xml_test_log_file, opts, timeout, num_jobs):
    getstatusoutput_mock = mocker.patch('subprocess.getstatusoutput')
    getstatusoutput_mock.return_value = (0,
                                         'foo1:bar1 / testdir1/test1\n'
                                         'foo1:bar1 / testdir1/test2\n'
                                         'foo2:bar2 / testdir2/test3\n'
                                         'foo2:bar2 / testdir2/test4')

    meta = TestMeta(MesonTest)
    mesontest = MesonTest('', output_file, opts, meta, timeout)
    mesontest.set_num_jobs(num_jobs)

    # Initialize test report that would normally be created by meson.
    JUnitXML.make_from_passed([]).write(xml_test_log_file)

    mocker.patch('subprocess.run')

    expected_kwargs = {
            'args': f'meson test testdir1/test1 testdir1/test2 testdir2/test3 testdir2/test4 -C {BUILD_DIR} -j {num_jobs} {opts}',
            'stderr': ANY,
            'stdout': ANY,
            'timeout': timeout,
            'check': False,
            'shell': True
            }

    mesontest._run_mesontest()

    subprocess.run.assert_called_once_with(**expected_kwargs)

def test__run_mesontest_skipped(mocker, output_file, xml_test_log_file):
    getstatusoutput_mock = mocker.patch('subprocess.getstatusoutput')
    getstatusoutput_mock.return_value = (0,
                                         'foo1:bar1 / testdir1/test1\n'
                                         'foo1:bar1 / testdir1/test2\n'
                                         'foo2:bar2 / testdir2/test3\n'
                                         'foo2:bar2 / testdir2/test4')

    skip_list = [
            SkippedSuite.make_from_dict(
                {
                    'name': 'foo1',
                    'file': 'file1',
                    'timestamp': '1970-01-01T00:00:00+00:00',
                    'cases': [
                            {
                                'name': 'foo1:bar1 / testdir1/test1',
                                'line': '1',
                                'os': ['8.0.0'],
                            },
                            {
                                'name': 'foo1:bar1 / testdir1/test2',
                                'line': '2'
                            }]}),
            SkippedSuite.make_from_dict(
                {
                    'name': 'foo2',
                    'file': 'file2',
                    'timestamp': '2000-01-01T00:00:00+00:00',
                    'cases': [
                            {
                                'name': 'foo2:bar2 / testdir2/test3',
                                'line': '1',
                                'os': ['7.1.0'],
                                'arch': ['x86_64']
                            }]})
            ]

    meta = TestMeta(MesonTest, skipped=skip_list)
    mesontest = MesonTest('', output_file, '', meta, None)

    # Initialize test report that would normally be created by meson.
    JUnitXML.make_from_passed([]).write(xml_test_log_file)

    mocker.patch('subprocess.run')

    expected_kwargs = {
            'args': f'meson test testdir2/test4 -C {BUILD_DIR} -j 1 ',
            'stderr': ANY,
            'stdout': ANY,
            'timeout': None,
            'check': False,
            'shell': True
            }

    mesontest._run_mesontest()

    subprocess.run.assert_called_once_with(**expected_kwargs)

def test_should_report_skipped_tests():
    assert MesonTest.should_report_skipped_tests()

def test_get_name_framework():
    assert MesonTest.get_name_framework() == 'meson'

def test__run_impl():
    assert MesonTest._run_impl == MesonTest._run_mesontest
