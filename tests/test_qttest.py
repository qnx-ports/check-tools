"""
Unit tests for catch2test.py
"""

from pathlib import Path
import pytest
import subprocess
from typing import Final
from unittest.mock import ANY

from check_utils import QtTest, Skipped
import common

REPORT_FILE: Final[str] = f'./tmp_{Path(__file__).stem}.xml'
OUTPUT_FILE: Final[str] = f'./tmp_{Path(__file__).stem}.txt'
BLACKLIST_FILE: Final[str] = './BLACKLIST'

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

@pytest.mark.parametrize('opts,timeout', [
    ('', None), ('--my-custom-opt1 --my-custom-opt2', None),
    ('', 300), ('--my-custom-opt1 --my-custom-opt2', 300)
    ])
def test__run_qttest(mocker, output_file, opts, timeout):
    qttest = QtTest('bin', REPORT_FILE, output_file, opts, None, timeout)

    mocker.patch('subprocess.run')

    expected_kwargs = {
            'args': f'./bin -o {REPORT_FILE},junitxml {opts} ',
            'stderr': ANY,
            'stdout': ANY,
            'timeout': timeout,
            'check': False,
            'shell': True
            }

    qttest._run_qttest()

    subprocess.run.assert_called_once_with(**expected_kwargs)

    assert not Path(BLACKLIST_FILE).exists()

def test__run_qttest_skipped1(mocker, output_file):
    skipped = Skipped.make_from_dict({'name': 'bin1'})
    qttest = QtTest('bin1', REPORT_FILE, output_file, '', skipped, None)

    mocker.patch('subprocess.run')

    expected_kwargs = {
            'args': f'./bin1 -o {REPORT_FILE},junitxml  ',
            'stderr': ANY,
            'stdout': ANY,
            'timeout': None,
            'check': False,
            'shell': True
            }

    qttest._run_qttest()

    subprocess.run.assert_called_once_with(**expected_kwargs)

    assert not Path(BLACKLIST_FILE).exists()

def test__run_qttest_skipped2(mocker, output_file, blacklist_file):
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
                            'arch': ['x86_64']
                        }]}]})
    qttest = QtTest('bin2', REPORT_FILE, output_file, '',
                            skipped, None)

    mocker.patch('subprocess.run')

    expected_kwargs = {
            'args': f'./bin2 -o {REPORT_FILE},junitxml  -skipblacklisted ',
            'stderr': ANY,
            'stdout': ANY,
            'timeout': None,
            'check': False,
            'shell': True
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

def test_get_name_framework():
    assert QtTest.get_name_framework() == 'qt-test'

def test__run_impl():
    assert QtTest._run_impl == QtTest._run_qttest
