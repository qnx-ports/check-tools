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
Provides data formats for tests to help communicate with the underlying test
framework, and convert to JUnitXML.
"""
from abc import ABC
from functools import cache
from typing import List, Optional

class Case(ABC):
    name: str = ''
    line: str = ''

    def __init__(self, name: str, line: str):
        assert isinstance(name, str)
        assert isinstance(line, str)
        self.name = name
        self.line = line

    def get_name(self) -> str:
        return self.name

    def get_line(self) -> str:
        return self.line

class ExecutedCase(Case, ABC):
    time: str = '0.0'
    assertions: str = '0'

    def __init__(self, name: str, line: str, time: str, assertions: str):
        super().__init__(name, line)

        assert isinstance(time, str)
        assert isinstance(assertions, str)
        self.time = time
        self.assertions = assertions

    def get_time(self):
        return self.time

    def get_assertions(self):
        return self.assertions

class Suite(ABC):
    name: str = ''
    file: str = ''
    timestamp: str = ''
    cases: List[Case]

    def __init__(self, name: str, file: str, timestamp: str, cases: List[Case]):
        assert isinstance(name, str)
        assert isinstance(file, str)
        assert isinstance(timestamp, str)
        assert isinstance(cases, list)
        self.name = name
        self.file = file
        self.timestamp = timestamp
        self.cases = cases

    def get_name(self):
        return self.name

    def get_file(self):
        return self.file

    def get_timestamp(self):
        return self.timestamp

    def get_case_names(self) -> List[str]:
        return [case.get_name() for case in self.cases]

    def get_cases(self):
        return self.cases

    def get_case(self, case_name) -> Optional[Case]:
        for case in self.cases:
            if case_name == case.get_name():
                return case
        return None

class Bin(ABC):
    name: str = ''
    suites: List[Suite] = []

    def __init__(self, name: str, suites: List[Suite]):
        assert isinstance(name, str)
        assert isinstance(suites, list)
        self.name = name
        self.suites = suites

    def get_name(self):
        return self.name

    def get_case_names(self):
        case_names = []
        for suite in self.suites:
            case_names += suite.get_case_names()
        return case_names

    def get_suite_names(self):
        return [suite.get_name() for suite in self.suites]

    def get_suites(self):
        return self.suites

    # Avoid iterating list when possible
    @cache
    def get_suite(self, suite_name) -> Optional[Suite]:
        for suite in self.suites:
            if suite.get_name() == suite_name:
                return suite
        return None

    def is_empty(self):
        if len(self.suites) != 0:
            for suite in self.suites:
                if len(suite.get_cases()) != 0:
                    return False
        return True
