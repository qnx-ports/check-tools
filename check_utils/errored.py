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
Provides data formats for errored tests to help convert to JUnitXML.
"""
from typing import Self, List

class ErroredCase:
    name: str = ''
    line: str = ''
    time: str = '0.0'
    assertions: str = '0'
    message: str = ''
    etype: str = ''

    def __init__(self, name: str, line: str, time: str,
                 assertions: str, message: str, etype: str) -> None:
        assert isinstance(name, str)
        assert isinstance(line, str)
        assert isinstance(time, str)
        assert isinstance(assertions, str)
        assert isinstance(message, str)
        assert isinstance(etype, str)
        self.name = name
        self.line = line
        self.time = time
        self.assertions = assertions
        self.message = message
        self.etype = etype

    def get_name(self):
        return self.name

    def get_line(self):
        return self.line

    def get_time(self):
        return self.time

    def get_assertions(self):
        return self.assertions

    def get_message(self):
        return self.message

    def get_etype(self):
        return self.etype

    @classmethod
    def make_from_dict(cls, case: dict) -> Self:
        """
        Create obj from the format:
        {
            'name': name
            'line': line
            'time': time
            'assertions': assertions
            'message': message
            'etype': etype
        }
        """
        name = case['name']
        line = case.get('line', '')
        time = case.get('time', '0.0')
        assertions = case.get('assertions', '0')
        message = case.get('message', '')
        etype = case.get('etype', '')
        return cls(name, line, time, assertions, message, etype)

class ErroredSuite:
    name: str = ''
    file: str = ''
    timestamp: str = ''
    cases: List[ErroredCase] = []

    def __init__(self, name: str, file: str, timestamp: str,
                 cases: List[ErroredCase]) -> None:
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

    def get_cases(self):
        return self.cases

    @classmethod
    def make_from_dict(cls, suite: dict) -> Self:
        """
        Create obj from the format:
        {
            'name': name
            'file': file
            'timestamp': timestamp
            'cases': [ %FailedCase% ]
        }
        """
        name = suite['name']
        file = suite.get('file', '')
        timestamp = suite.get('timestamp', '')
        cases = [ErroredSuite.make_from_dict(case) for case in suite.get('cases', ())]
        return cls(name, file, timestamp, cases)
