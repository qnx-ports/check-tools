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

from check_utils import GTest, Skipped, JUnitXML, ErroredCase, ErroredSuite
import common

REPORT_FILE: Final[str] = f'./tmp_{Path(__file__).stem}.xml'
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

def mkstemp_mock(suffix: str):
    # Spoof a test run...
    tmp_xml = JUnitXML.make_from_passed([])
    tmp_xml.write(MKSTEMP_REPORT_FILE)
    return (os.open(MKSTEMP_REPORT_FILE, os.O_WRONLY | os.O_CREAT), MKSTEMP_REPORT_FILE)

@patch.object(tempfile, 'mkstemp', mkstemp_mock)
@pytest.mark.parametrize('opts,timeout,blurb', [
    ('', None, ''),
    ('--my-custom-opt1 --my-custom-opt2', 300, 'Run this program with --check_for_leaks to enable custom leak checking in the tests.\n'),
    ('-a', 1800, 'Running main() from googletest/googletest/src/gtest_main.cc\n')
    ])
def test__run_gtest(mocker, report_file, output_file, opts, timeout, blurb):
    getstatusoutput_mock = mocker.patch('subprocess.getstatusoutput')
    getstatusoutput_mock.return_value = (0,
                                         blurb +
                                         'Foo.\n'
                                         ' Test1\n'
                                         ' Test2\n'
                                         'Bar.\n'
                                         ' 3tseT\n'
                                         ' Ttse4')

    gtest = GTest('bin', report_file, output_file, opts,
                  None, timeout)

    mocker.patch('subprocess.run')

    expected_kwargs1 = {
            'args': f'./bin --gtest_output="xml:{MKSTEMP_REPORT_FILE}" --gtest_filter="Foo.Test1" {opts}',
            'stderr': ANY,
            'stdout': ANY,
            'timeout': timeout,
            'check': True,
            'shell': True
            }

    expected_kwargs2 = {
            'args': f'./bin --gtest_output="xml:{MKSTEMP_REPORT_FILE}" --gtest_filter="Foo.Test2" {opts}',
            'stderr': ANY,
            'stdout': ANY,
            'timeout': timeout,
            'check': True,
            'shell': True
            }

    expected_kwargs3 = {
            'args': f'./bin --gtest_output="xml:{MKSTEMP_REPORT_FILE}" --gtest_filter="Bar.3tseT" {opts}',
            'stderr': ANY,
            'stdout': ANY,
            'timeout': timeout,
            'check': True,
            'shell': True
            }

    expected_kwargs4 = {
            'args': f'./bin --gtest_output="xml:{MKSTEMP_REPORT_FILE}" --gtest_filter="Bar.Ttse4" {opts}',
            'stderr': ANY,
            'stdout': ANY,
            'timeout': timeout,
            'check': True,
            'shell': True
            }

    gtest._run_gtest()

    subprocess.run.assert_any_call(**expected_kwargs1)
    subprocess.run.assert_any_call(**expected_kwargs2)
    subprocess.run.assert_any_call(**expected_kwargs3)
    subprocess.run.assert_any_call(**expected_kwargs4)

    assert not Path(MKSTEMP_REPORT_FILE).exists()
    assert Path(report_file).exists()

@patch.object(tempfile, 'mkstemp', mkstemp_mock)
def test__run_gtest_skipped1(mocker, report_file, output_file):
    getstatusoutput_mock = mocker.patch('subprocess.getstatusoutput')
    getstatusoutput_mock.return_value = (0,
                                         'Foo.\n'
                                         ' Test1\n'
                                         ' Test2\n'
                                         'Bar.\n'
                                         ' 3tseT\n'
                                         ' Ttse4')

    skipped = Skipped.make_from_dict({'name': 'bin1'})
    gtest = GTest('bin1', report_file, output_file, '',
                  skipped, None)

    mocker.patch('subprocess.run')

    expected_kwargs1 = {
            'args': f'./bin1 --gtest_output="xml:{MKSTEMP_REPORT_FILE}" --gtest_filter="Foo.Test1" ',
            'stderr': ANY,
            'stdout': ANY,
            'timeout': None,
            'check': True,
            'shell': True
            }

    expected_kwargs2 = {
            'args': f'./bin1 --gtest_output="xml:{MKSTEMP_REPORT_FILE}" --gtest_filter="Foo.Test2" ',
            'stderr': ANY,
            'stdout': ANY,
            'timeout': None,
            'check': True,
            'shell': True
            }

    expected_kwargs3 = {
            'args': f'./bin1 --gtest_output="xml:{MKSTEMP_REPORT_FILE}" --gtest_filter="Bar.3tseT" ',
            'stderr': ANY,
            'stdout': ANY,
            'timeout': None,
            'check': True,
            'shell': True
            }

    expected_kwargs4 = {
            'args': f'./bin1 --gtest_output="xml:{MKSTEMP_REPORT_FILE}" --gtest_filter="Bar.Ttse4" ',
            'stderr': ANY,
            'stdout': ANY,
            'timeout': None,
            'check': True,
            'shell': True
            }

    gtest._run_gtest()

    subprocess.run.assert_any_call(**expected_kwargs1)
    subprocess.run.assert_any_call(**expected_kwargs2)
    subprocess.run.assert_any_call(**expected_kwargs3)
    subprocess.run.assert_any_call(**expected_kwargs4)

    assert not Path(MKSTEMP_REPORT_FILE).exists()
    assert Path(report_file).exists()

@patch.object(tempfile, 'mkstemp', mkstemp_mock)
def test__run_gtest_skipped2(mocker, report_file, output_file):
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
                            'arch': ['x86_64']
                        }]}]})
    gtest = GTest('bin2', report_file, output_file, '',
                  skipped, None)

    mocker.patch('subprocess.run')

    expected_kwargs = {
            'args': f'./bin2 --gtest_output="xml:{MKSTEMP_REPORT_FILE}" --gtest_filter="Bar.Ttse4" ',
            'stderr': ANY,
            'stdout': ANY,
            'timeout': None,
            'check': True,
            'shell': True
            }

    gtest._run_gtest()

    subprocess.run.assert_called_once_with(**expected_kwargs)

    assert not Path(MKSTEMP_REPORT_FILE).exists()
    assert Path(report_file).exists()

@patch.object(tempfile, 'mkstemp', mkstemp_mock)
def test__run_gtest_errored(mocker, report_file, output_file):
    getstatusoutput_mock = mocker.patch('subprocess.getstatusoutput')
    getstatusoutput_mock.return_value = (0,
                                         'Foo.\n'
                                         ' Test1\n'
                                         ' Test2\n'
                                         'Bar.\n'
                                         ' 3tseT\n'
                                         ' Ttse4')

    gtest = GTest('bin1', report_file, output_file, '',
                  None, None)

    run_mock = mocker.patch('subprocess.run')
    run_mock.side_effect = subprocess.CalledProcessError('returncode', 'cmd')

    expected_kwargs1 = {
            'args': f'./bin1 --gtest_output="xml:{MKSTEMP_REPORT_FILE}" --gtest_filter="Foo.Test1" ',
            'stderr': ANY,
            'stdout': ANY,
            'timeout': None,
            'check': True,
            'shell': True
            }

    expected_kwargs2 = {
            'args': f'./bin1 --gtest_output="xml:{MKSTEMP_REPORT_FILE}" --gtest_filter="Foo.Test2" ',
            'stderr': ANY,
            'stdout': ANY,
            'timeout': None,
            'check': True,
            'shell': True
            }

    expected_kwargs3 = {
            'args': f'./bin1 --gtest_output="xml:{MKSTEMP_REPORT_FILE}" --gtest_filter="Bar.3tseT" ',
            'stderr': ANY,
            'stdout': ANY,
            'timeout': None,
            'check': True,
            'shell': True
            }

    expected_kwargs4 = {
            'args': f'./bin1 --gtest_output="xml:{MKSTEMP_REPORT_FILE}" --gtest_filter="Bar.Ttse4" ',
            'stderr': ANY,
            'stdout': ANY,
            'timeout': None,
            'check': True,
            'shell': True
            }

    gtest._run_gtest()

    subprocess.run.assert_any_call(**expected_kwargs1)
    subprocess.run.assert_any_call(**expected_kwargs2)
    subprocess.run.assert_any_call(**expected_kwargs3)
    subprocess.run.assert_any_call(**expected_kwargs4)

    assert gtest.errored_tests == ['Foo.Test1', 'Foo.Test2', 'Bar.3tseT', 'Bar.Ttse4']
    assert len(gtest.errored) == 2 # 2 suites

    # tmp_file still exists as a result of mkstemp_mock.
    #assert not Path(MKSTEMP_REPORT_FILE).exists()
    # report_file must still be created for _report_errored_tests to succeed.
    assert Path(report_file).exists()

def test__report_skipped_tests(mocker, report_file):
    getstatusoutput_mock = mocker.patch('subprocess.getstatusoutput')
    getstatusoutput_mock.return_value = (0,
                                         'Foo.\n'
                                         ' Test1\n'
                                         ' Test2\n'
                                         'Bar.\n'
                                         ' 3tseT\n'
                                         ' Ttse4')

    skipped = Skipped.make_from_dict({
        'name': 'bin',
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

def test__report_errored_tests(mocker, report_file):
    getstatusoutput_mock = mocker.patch('subprocess.getstatusoutput')
    getstatusoutput_mock.return_value = (0,
                                         'Foo.\n'
                                         ' Test1\n'
                                         ' Test2\n'
                                         'Bar.\n'
                                         ' 3tseT\n'
                                         ' Ttse4')

    gtest = GTest('bin', report_file, OUTPUT_FILE, '',
                  None, None)

    errored_case1 = ErroredCase('Test1', '1', '0.9', '2', 'Permission denied', 'EACCES')
    errored_case2 = ErroredCase('Test2', '2', '1.2', '3', '[1]    420683 floating point exception (core dumped)', 'SIGFPE')

    errored_suite1 = ErroredSuite('Foo', 'file1', '1970-01-01T00:00:00+00:00', [errored_case1, errored_case2])
    gtest.errored.append(errored_suite1)
    gtest.errored_tests.append('Foo.Test1')
    gtest.errored_tests.append('Foo.Test2')

    errored_case3 = ErroredCase('3tseT', '1', '2.1', '1', '[1]    421284 segmentation fault (core dumped)', 'SIGSEGV')

    errored_suite2 = ErroredSuite('Bar', 'file2', '2000-01-01T00:00:00+00:00', [errored_case3])
    gtest.errored.append(errored_suite2)
    gtest.errored_tests.append('Bar.3tseT')

    # Spoof a test run...
    report_xml = JUnitXML.make_from_passed([])
    report_xml.write(report_file)

    gtest._report_errored_tests()
    errored_xml = JUnitXML(file=report_file)
    assert errored_xml.tree.getroot().get('errors', '-1') == '3'

def test_get_name_framework():
    assert GTest.get_name_framework() == 'googletest'

def test__run_impl():
    assert GTest._run_impl == GTest._run_gtest
