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
Provides data formats for failed tests to help convert to JUnitXML.
"""
from typing import Self, List
from .jtype import ExecutedCase, Suite

class FailedCase(ExecutedCase):
    message: str = ''
    ftype: str = ''

    def __init__(self, name: str, line: str, time: str,
                 assertions: str, message: str, ftype: str) -> None:
        super().__init__(name, line, time, assertions)

        assert isinstance(message, str)
        assert isinstance(ftype, str)
        self.message = message
        self.ftype = ftype

    def get_message(self):
        return self.message

    def get_ftype(self):
        return self.ftype

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
            'ftype': ftype
        }
        """
        name = case['name']
        line = case.get('line', '')
        time = case.get('time', '0.0')
        assertions = case.get('assertions', '0')
        message = case.get('message', '')
        ftype = case.get('ftype', '')
        return cls(name, line, time, assertions, message, ftype)

class FailedSuite(Suite):

    def __init__(self, name: str, file: str, timestamp: str,
                 cases: List[FailedCase]) -> None:
        super().__init__(name, file, timestamp, cases)

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
        cases = [FailedSuite.make_from_dict(case) for case in suite.get('cases', ())]
        return cls(name, file, timestamp, cases)
