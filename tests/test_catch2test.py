"""
Unit tests for catch2test.py
"""

from pathlib import Path
import pytest
import subprocess
from typing import Final
from unittest.mock import ANY

from check_utils import Catch2Test, Skipped
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
def test__run_catch2test(mocker, output_file, opts, timeout):
    catch2test = Catch2Test('bin', REPORT_FILE, output_file, opts,
                  None, timeout)

    mocker.patch('subprocess.run')

    expected_kwargs = {
            'args': f'./bin --reporter xml::out={REPORT_FILE} {opts} ',
            'stderr': ANY,
            'stdout': ANY,
            'timeout': timeout,
            'check': False,
            'shell': True
            }

    catch2test._run_catch2test()

    subprocess.run.assert_called_once_with(**expected_kwargs)

def test__run_catch2test_skipped1(mocker, output_file):
    skipped = Skipped.make_from_dict({'name': 'bin1'})
    catch2test = Catch2Test('bin1', REPORT_FILE, output_file, '',
                       skipped, None)

    mocker.patch('subprocess.run')

    expected_kwargs = {
            'args': f'./bin1 --reporter xml::out={REPORT_FILE}  ',
            'stderr': ANY,
            'stdout': ANY,
            'timeout': None,
            'check': False,
            'shell': True
            }

    catch2test._run_catch2test()

    subprocess.run.assert_called_once_with(**expected_kwargs)

def test__run_catch2test_skipped2(mocker, output_file):
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
    catch2test = Catch2Test('bin2', REPORT_FILE, output_file, '',
                            skipped, None)

    mocker.patch('subprocess.run')

    expected_kwargs = {
            'args': f'./bin2 --reporter xml::out={REPORT_FILE}  *,~case1,~case2,~case3 ',
            'stderr': ANY,
            'stdout': ANY,
            'timeout': None,
            'check': False,
            'shell': True
            }

    catch2test._run_catch2test()

    subprocess.run.assert_called_once_with(**expected_kwargs)

def test_get_name_framework():
    assert Catch2Test.get_name_framework() == 'catch2'

def test__run_impl():
    assert Catch2Test._run_impl == Catch2Test._run_catch2test
