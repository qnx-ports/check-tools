"""
Unit tests for pytest.py
"""

from pathlib import Path
import pytest
import subprocess
from typing import Final
from unittest.mock import ANY

from check_utils import PyTest, SkippedSuite, BUILD_DIR
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

    yield REPORT_FILE

    # Teardown
    if (report_path.exists()):
        report_path.unlink()

@pytest.mark.parametrize('opts,timeout', [
    ('', None), ('--my-custom-opt1 --my-custom-opt2', None),
    ('', 300), ('--my-custom-opt1 --my-custom-opt2', 300)
    ])
def test__run_pytest(mocker, report_file, output_file, opts, timeout):
    pytest = PyTest(REPORT_FILE, output_file, opts,
                          [], timeout)

    mocker.patch('subprocess.run')

    expected_kwargs = {
            'args': f'pytest --junit-xml={report_file} {opts} ',
            'stderr': ANY,
            'stdout': ANY,
            'timeout': timeout,
            'check': False,
            'shell': True
            }

    pytest._run_pytest()

    subprocess.run.assert_called_once_with(**expected_kwargs)

def test__run_mesontest_skipped(mocker, report_file, output_file):
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
    pytest = PyTest(REPORT_FILE, output_file, '',
                          skip_list, None)

    mocker.patch('subprocess.run')

    expected_kwargs = {
            'args': f'pytest --junit-xml={report_file}  -k "not test_foo1 and not test_foo2 and not test_foo3" ',
            'stderr': ANY,
            'stdout': ANY,
            'timeout': None,
            'check': False,
            'shell': True
            }

    pytest._run_pytest()

    subprocess.run.assert_called_once_with(**expected_kwargs)

def test_get_name_framework():
    assert PyTest.get_name_framework() == 'pytest'

def test__run_impl():
    assert PyTest._run_impl == PyTest._run_pytest
