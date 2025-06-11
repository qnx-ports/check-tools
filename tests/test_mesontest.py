"""
Unit tests for mesontest.py
"""

from pathlib import Path
import pytest
import subprocess
from typing import Final
from unittest.mock import ANY

from check_utils import MesonTest, SkippedSuite, BUILD_DIR
import common

REPORT_FILE: Final[str] = f'./tmp_{Path(__file__).stem}.xml'
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
def report_file():
    report_path = Path(REPORT_FILE)

    # Setup
    if (report_path.exists()):
        report_path.unlink()
    # Create empty file as workaround for rename.
    xml_test_log = BUILD_DIR.joinpath(MesonTest.XML_TEST_LOG)
    if xml_test_log.parent.is_file():
        xml_test_log.parent.rmdir()
    xml_test_log.parent.mkdir(parents=True, exist_ok=True)
    xml_test_log.touch()

    yield REPORT_FILE

    # Teardown
    if (report_path.exists()):
        report_path.unlink()
    # The file should have been destroyed.
    xml_test_log.parent.rmdir()

@pytest.mark.parametrize('opts,timeout', [
    ('', None), ('--my-custom-opt1 --my-custom-opt2', None),
    ('', 300), ('--my-custom-opt1 --my-custom-opt2', 300)
    ])
def test__run_mesontest(mocker, report_file, output_file, opts, timeout):
    getstatusoutput_mock = mocker.patch('subprocess.getstatusoutput')
    getstatusoutput_mock.return_value = (0,
                                         'foo1:bar1 / testdir1/test1\n'
                                         'foo1:bar1 / testdir1/test2\n'
                                         'foo2:bar2 / testdir2/test3\n'
                                         'foo2:bar2 / testdir2/test4')

    mesontest = MesonTest(REPORT_FILE, output_file, opts,
                          [], timeout)

    mocker.patch('subprocess.run')

    expected_kwargs = {
            'args': f'meson test testdir1/test1 testdir1/test2 testdir2/test3 testdir2/test4 -C {BUILD_DIR} {opts}',
            'stderr': ANY,
            'stdout': ANY,
            'timeout': timeout,
            'check': False,
            'shell': True
            }

    mesontest._run_mesontest()

    subprocess.run.assert_called_once_with(**expected_kwargs)

    assert Path(report_file).is_file()

def test__run_mesontest_skipped(mocker, report_file, output_file):
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
    mesontest = MesonTest(REPORT_FILE, output_file, '',
                          skip_list, None)

    mocker.patch('subprocess.run')

    expected_kwargs = {
            'args': f'meson test testdir2/test4 -C {BUILD_DIR} ',
            'stderr': ANY,
            'stdout': ANY,
            'timeout': None,
            'check': False,
            'shell': True
            }

    mesontest._run_mesontest()

    subprocess.run.assert_called_once_with(**expected_kwargs)

    assert Path(report_file).is_file()

def test_get_name_framework():
    assert MesonTest.get_name_framework() == 'meson'

def test__run_impl():
    assert MesonTest._run_impl == MesonTest._run_mesontest
