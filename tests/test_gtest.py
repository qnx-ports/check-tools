"""
Unit tests for gtest.py
"""

from pathlib import Path
import pytest
import subprocess
from typing import Final
from unittest.mock import ANY

from check_utils import GTest, Skipped, JUnitXML

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
def test__run_gtest(mocker, output_file, opts, timeout):
    gtest = GTest('bin', REPORT_FILE, output_file, opts,
                  None, timeout)

    mocker.patch('subprocess.run')

    expected_kwargs = {
            'args': f'./bin --gtest_output="xml:{REPORT_FILE}" --gtest_filter="*-" {opts}',
            'stderr': ANY,
            'stdout': ANY,
            'timeout': timeout,
            'check': False,
            'shell': True
            }

    gtest._run_gtest()

    subprocess.run.assert_called_once_with(**expected_kwargs)

def test__run_gtest_skipped1(mocker, output_file):
    skipped = Skipped.make_from_dict({'name': 'bin1'})
    gtest = GTest('bin1', REPORT_FILE, output_file, '',
                  skipped, None)

    mocker.patch('subprocess.run')

    expected_kwargs = {
            'args': f'./bin1 --gtest_output="xml:{REPORT_FILE}" --gtest_filter="*-" ',
            'stderr': ANY,
            'stdout': ANY,
            'timeout': None,
            'check': False,
            'shell': True
            }

    gtest._run_gtest()

    subprocess.run.assert_called_once_with(**expected_kwargs)

def test__run_gtest_skipped2(mocker, output_file):
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
    gtest = GTest('bin2', REPORT_FILE, output_file, '',
                  skipped, None)

    mocker.patch('subprocess.run')

    expected_kwargs = {
            'args': f'./bin2 --gtest_output="xml:{REPORT_FILE}" --gtest_filter="*-suite1.case1:suite1.case2:suite2.case3" ',
            'stderr': ANY,
            'stdout': ANY,
            'timeout': None,
            'check': False,
            'shell': True
            }

    gtest._run_gtest()

    subprocess.run.assert_called_once_with(**expected_kwargs)

def test__report_skipped_tests(report_file):
    skipped = Skipped.make_from_dict({
        'name': 'bin',
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

    gtest = GTest('bin', report_file, OUTPUT_FILE, '',
                  skipped, None)

    # Spoof a test run...
    report_xml = JUnitXML.make_from_passed([])
    report_xml.write(report_file)

    gtest._report_skipped_tests()
    skipped_xml = JUnitXML(file=report_file)
    assert skipped_xml.tree.getroot().get('skipped', '-1') == '3'

@pytest.fail('Functionality not yet implemented.')
def test__report_errored_tests():
    pass

def test_get_name_framework():
    assert GTest.get_name_framework() == 'googletest'

def test__run_impl():
    assert GTest._run_impl == GTest._run_gtest
