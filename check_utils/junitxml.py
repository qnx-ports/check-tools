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
Tools for parsing logs and creating/manipulating JUnitXML files.
"""

import copy
import datetime
from pathlib import Path
from typing import List, Optional, Self
import xml.etree.ElementTree as ET

from .definitions import IllegalArgumentError
from .jtype.skipped import SkippedSuite
from .jtype.failed import FailedSuite
from .jtype.errored import ErroredSuite
from .jtype.passed import PassedSuite

class JUnitXML:
    _tree: ET.ElementTree = None

    def __init__(self,
                 file: Optional[str] = None,
                 tree: Optional[ET.ElementTree] = None):
        if tree is not None:
            self._tree = tree
        elif file is None:
            self._tree = ET.ElementTree(element=JUnitXML.create_empty_testsuites())
        elif not (Path(file).exists() and Path(file).is_file()):
            raise IllegalArgumentError('JUnitXML supplied invalid '
                                                   'file path.')
        else:
            self._tree = ET.parse(file)

        if self._tree is not None:
            JUnitXML._standardize_tree(self._tree)

    def load(self, file):
        if not Path(file).exists() and Path(file).is_file():
            raise IllegalArgumentError('JUnitXML supplied invalid '
                                                   'file path.')
        else:
            self._tree = ET.parse(file)

        if self._tree is not None:
            JUnitXML._standardize_tree(self._tree)

    # --- PUBLIC ---
    def write(self, file):
        self._balance(self._tree.getroot())
        self._tree.write(file)

    def is_success(self) -> bool:
        """
        Check if testing succeeded based on this report.

        @return True if there were no failures or errors,
                False otherwise.
        """
        root = self.tree.getroot()
        return (root.get('failures', '0') == '0') \
                and (root.get('errors', '0') == '0')

    def get_tree(self) -> ET.ElementTree:
        self._balance(self._tree.getroot())
        return self._tree

    def set_tree(self, tree: ET.ElementTree) -> None:
        self._tree = tree

    tree = property(fget=get_tree, fset=set_tree)

    @classmethod
    def make_from_skipped(cls, suites: List[SkippedSuite]) -> Self:
        suites_elem: ET.Element = JUnitXML.create_empty_testsuites()

        for suite in suites:
            suite_elem = JUnitXML.create_empty_testsuite(suite.get_name(),
                                                         suite.get_file())

            suite_elem.set('timestamp', suite.get_timestamp())

            suites_elem.append(suite_elem)

            for case in suite.get_cases():
                skipped_elem = ET.Element('skipped',
                                          attrib={
                                              'message': case.get_message()
                                              })
                case_elem = JUnitXML.create_empty_testcase(case.get_name(),
                                                           suite.get_name(),
                                                           suite.get_file(),
                                                           case.get_line())
                case_elem.append(skipped_elem)

                suite_elem.append(case_elem)

        return cls(tree=ET.ElementTree(suites_elem))

    @classmethod
    def make_from_failed(cls, suites: List[FailedSuite]) -> Self:
        suites_elem: ET.Element = JUnitXML.create_empty_testsuites()

        for suite in suites:
            suite_elem = JUnitXML.create_empty_testsuite(suite.get_name(),
                                                         suite.get_file())

            suite_elem.set('timestamp', suite.get_timestamp())

            suites_elem.append(suite_elem)

            for case in suite.get_cases():
                failed_elem = ET.Element('failure',
                                          attrib={
                                              'message': case.get_message(),
                                              'type': case.get_ftype()
                                              })
                case_elem = JUnitXML.create_empty_testcase(case.get_name(),
                                                           suite.get_name(),
                                                           suite.get_file(),
                                                           case.get_line())

                case_elem.set('time', case.get_time())
                case_elem.set('assertions', case.get_assertions())
                case_elem.append(failed_elem)

                suite_elem.append(case_elem)

        return cls(tree=ET.ElementTree(suites_elem))

    @classmethod
    def make_from_errored(cls, suites: List[ErroredSuite]) -> Self:
        suites_elem: ET.Element = JUnitXML.create_empty_testsuites()

        for suite in suites:
            suite_elem = JUnitXML.create_empty_testsuite(suite.get_name(),
                                                         suite.get_file())

            suite_elem.set('timestamp', suite.get_timestamp())

            suites_elem.append(suite_elem)

            for case in suite.get_cases():
                errored_elem = ET.Element('error',
                                          attrib={
                                              'message': case.get_message(),
                                              'type': case.get_etype()
                                              })
                case_elem = JUnitXML.create_empty_testcase(case.get_name(),
                                                           suite.get_name(),
                                                           suite.get_file(),
                                                           case.get_line())

                case_elem.set('time', case.get_time())
                case_elem.set('assertions', case.get_assertions())
                case_elem.append(errored_elem)

                suite_elem.append(case_elem)

        return cls(tree=ET.ElementTree(suites_elem))

    @classmethod
    def make_from_passed(cls, suites: List[PassedSuite]) -> Self:
        suites_elem: ET.Element = JUnitXML.create_empty_testsuites()

        for suite in suites:
            suite_elem = JUnitXML.create_empty_testsuite(suite.get_name(),
                                                         suite.get_file())

            suite_elem.set('timestamp', suite.get_timestamp())

            suites_elem.append(suite_elem)

            for case in suite.get_cases():
                case_elem = JUnitXML.create_empty_testcase(case.get_name(),
                                                           suite.get_name(),
                                                           suite.get_file(),
                                                           case.get_line())

                case_elem.set('time', case.get_time())
                case_elem.set('assertions', case.get_assertions())

                suite_elem.append(case_elem)

        return cls(tree=ET.ElementTree(suites_elem))

    @classmethod
    def create_empty_testsuites(cls) -> ET.Element:
        return ET.Element('testsuites',
                          attrib={'tests':'0',
                                  'failures': '0',
                                  'skipped': '0',
                                  'errors': '0',
                                  'assertions':'0',
                                  'time':'0.0'})

    @classmethod
    def create_empty_testsuite(cls, name: str, file: str) -> ET.Element:
        return ET.Element('testsuite',
                          attrib={'name': name,
                                  'tests': '0',
                                  'failures': '0',
                                  'skipped': '0',
                                  'errors': '0',
                                  'assertions': '0',
                                  'time': '0.0',
                                  'file': file})

    @classmethod
    def create_empty_testcase(cls,
                              name: str,
                              suite: str,
                              file: str,
                              line: str) -> ET.Element:
        return ET.Element('testcase',
                          attrib={'name': name,
                                  'classname': suite,
                                  'assertions': '0',
                                  'time': '0.0',
                                  'file': file,
                                  'line': line})

    # --- OPPERATORS ---
    def __add__(self, other) -> Self:
        """
        Add two JUnitXML objects. Avoid in favour of __iadd__ for better
        performance.
        """
        if not isinstance(other, JUnitXML):
            raise NotImplementedError('Addition with invalid type.')

        tree = copy.deepcopy(self._tree)
        JUnitXML._iadd(tree.tree, other.tree)

        return JUnitXML(tree=tree)

    __radd__ = __add__

    def __iadd__(self, other) -> Self:
        """
        Add two JUnitXML objects and assign to self.
        """
        if not isinstance(other, JUnitXML):
            raise NotImplementedError('Addition with invalid type.')

        JUnitXML._iadd(self._tree, other.tree)

        return self

    # --- PRIVATE ---
    @classmethod
    def _iadd(cls,
              tree1: ET.ElementTree,
              tree2: ET.ElementTree) -> ET.ElementTree:
        """
        Adds contents of tree2 to tree1.

        @param tree1: JUnitXML tree to add.
        @param tree2: JUnitXML tree to add.
        @return Combined JUnitXML tree (tree1).
        """
        root1 = tree1.getroot()

        root2 = tree2.getroot()

        # The root of JUnitXML files is usually testsuites, but sometimes
        # testsuite if there is only one testsuite in the XML file.
        if root1.tag == 'testsuites' \
                and root2.tag == 'testsuites':
            # Add all testsuites that don't already exist from root2 to root1.
            for suite2 in root2.findall('testsuite'):
                suite1 = root1.find("./testsuite"
                                    f"[@name='{suite2.get('name', '')}']")
                if suite1 is None:
                    root1.append(suite2)
                else:
                    # Assume testcases don't already exist. There is no good way
                    # to handle it if they do.
                    suite1.extend(suite2)
        elif root1.tag == 'testsuite' \
                and root2.tag == 'testsuites':
            # We won't normally get here.
            #
            # Add elements to root2 and replace root1.
            # This is so that we can avoid extra work and reuse the "name"
            # attribute from root2.
            temp_root = copy.copy(root2)
            temp_root.append(root1)

            root1 = temp_root
            tree1._setroot(root1)
        elif root1.tag == 'testsuites' \
                and root2.tag == 'testsuite':
            # We only have one testsuite to add to the root1 report.
            root1.append(root2)
        elif root1.tag == 'testsuite' \
                and root2.tag == 'testsuite':
            # Create an empty test_suites element to be populated later.
            # We have no reliable way to decide on the "name" attribute.
            temp_root = ET.Element('testsuites')
            temp_root.append(root1)
            temp_root.append(root2)

            root1 = temp_root
            tree1._setroot(root1)
        else:
            raise RuntimeError('Report in bad format.')

        return tree1

    @classmethod
    def _balance(cls, test_suites: ET.Element) -> None:
        """
        Ensure all attributes of 'testsuites' element are accumulated from
        test cases.
        """
        # Update root element to latest timestamp. Timestamp is in ISO 8601,
        # so it must be converted to a simpler format before comparison.
        # These only come from testsuite. No reason to update anything else.
        zero_timestamp = '1970-01-01T00:00:00+00:00'
        timestamp = JUnitXML._convert_iso_timestamp(
                test_suites.get(
                    'timestamp',
                    zero_timestamp
                    ))
        for elem in test_suites.findall('./testsuite[@timestamp]'):
            ts = elem.get('timestamp', zero_timestamp)
            local_timestamp = JUnitXML._convert_iso_timestamp(
                    ts if len(ts) != 0 else zero_timestamp)
            if float(timestamp) < float(local_timestamp):
                timestamp = local_timestamp

        test_cases = 0
        failed = 0
        errored = 0
        skipped = 0
        time = 0.0
        assertions = 0
        for test_suite in test_suites.findall('./testsuite'):
            suite_test_cases = 0
            suite_failed = 0
            suite_errored = 0
            suite_skipped = 0
            suite_assertions = 0
            suite_time = 0.0

            suite_test_cases = len(test_suite.findall('./testcase'))

            suite_failed = len(test_suite.findall(
                './testcase//failure'))

            suite_errored = len(test_suite.findall(
                './testcase//error'))

            suite_skipped = len(test_suite.findall(
                './testcase//skipped'))

            for test_case in test_suite.findall('./testcase'):
                a = test_case.get('assertions', '')
                suite_assertions += int(a if a.isnumeric() else 0)
                t = test_case.get('time', '')
                suite_time += float(t if t.isnumeric() else 0.0)

            test_suite.set('tests', str(suite_test_cases))
            test_suite.set('failures', str(suite_failed))
            test_suite.set('errors', str(suite_errored))
            test_suite.set('skipped', str(suite_skipped))
            test_suite.set('assertions', str(suite_assertions))
            test_suite.set('time', str(suite_time))
            test_suite.set('assertions', str(suite_assertions))

            time += suite_time
            assertions += suite_assertions
            test_cases += suite_test_cases
            failed += suite_failed
            errored += suite_errored
            skipped += suite_skipped

        test_suites.set('tests', str(test_cases))
        test_suites.set('failures', str(failed))
        test_suites.set('errors', str(errored))
        test_suites.set('skipped', str(skipped))
        test_suites.set('assertions', str(assertions))
        test_suites.set('time', str(time))
        test_suites.set('timestamp', str(datetime.datetime\
                .fromtimestamp(timestamp).isoformat()))

    @classmethod
    def _convert_iso_timestamp(cls, iso: str):
        """
        Converts an ISO 8601 date string to a UTC timestamp.

        @param iso_date: date in ISO 8601 format.
        @return UTC timestamp.
        """
        iso_date = datetime.datetime.fromisoformat(iso)
        utc_ts = iso_date.replace(tzinfo=datetime.timezone.utc)
        return utc_ts.timestamp()

    @classmethod
    def _standardize_tree(cls, tree: ET.ElementTree):
        root = tree.getroot()
        if (root.tag != 'testsuite') and (root.tag != 'testsuites'):
            raise IllegalArgumentError('Provided XML file is not in JUnitXML '
                                       'format.')
        if root.tag == 'testsuite':
            # Harvest attrib, remove the test suite and file name.
            attrib = root.attrib
            attrib.pop('name', None)
            attrib.pop('file', None)
            temp_root = ET.Element('testsuites', attrib=attrib)

            temp_root.append(root)

            root = temp_root
            tree._setroot(root)
