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
Provides data formats for skipped tests to help communicate with the underlying
test framework, and convert to JUnitXML.
"""
from typing import List, Optional, Self

from ..system_spec import SystemSpec
from .jtype import Case, Suite, Bin

class SkippedCase(Case):
    os: List[str] = []
    arch: List[str] = []
    message: str = ''

    def __init__(self, name: str, line: str, os: List[str], arch: List[str],
                 message: Optional[str] = None):
        super().__init__(name, line)

        assert isinstance(os, list)
        assert isinstance(arch, list)
        self.os = os
        self.arch = arch
        self.message = message if message is not None else self._format_message(os, arch)

    def get_os(self) -> List[str]:
        return self.os

    def get_arch(self) -> List[str]:
        return self.arch

    def _format_message(self, os: List[str], arch: List[str]):
        return 'Skipped for '\
               + ('/'.join(os) if len(os) != 0 else 'all SDPs')\
               + ' on '\
               + ('/'.join(arch) if len(arch) != 0 else 'all archs')\
               + '.'

    def get_message(self) -> str:
        return self.message

    def is_match(self, spec: SystemSpec) -> bool:
        return (len(self.os) == 0 and len(self.arch) == 0) \
                or spec.get_os() in self.os \
                or spec.get_arch() in self.arch

    def filter_tests(self, spec: SystemSpec) -> Optional[Self]:
        if self.is_match(spec):
            return self
        else:
            return None

    @classmethod
    def make_from_dict(cls, case: dict) -> Self:
        """
        Create obj from the format:
        {
            'name': name
            'line': line
            'os': [ os1, os2 ]
            'arch': [ arch1, arch2 ]
        }
        """
        name = case['name']
        line = case.get('line', '')
        os = case.get('os', [])
        arch = case.get('arch', [])
        return cls(name, line, os, arch)

class SkippedSuite(Suite):

    def __init__(self, name: str, file: str, timestamp: str,
                 cases: List[SkippedCase]):
        super().__init__(name, file, timestamp, cases)

    def filter_tests(self, spec: SystemSpec) -> Optional[Self]:
        new_cases = []
        for case in self.cases:
            s = case.filter_tests(spec)
            if s is not None:
                new_cases.append(s)
        self.cases = new_cases

        if len(self.cases) != 0:
            return self
        else:
            return None

    @classmethod
    def make_from_dict(cls, suite: dict) -> Self:
        """
        Create obj from the format:
        {
            'name': name
            'file': file
            'timestamp': timestamp
            'cases': [ %SkippedCase% ]
        }
        """
        name = suite['name']
        file = suite.get('file', '')
        timestamp = suite.get('timestamp', '')
        cases = [SkippedCase.make_from_dict(case) for case in suite.get('cases', ())]
        return cls(name, file, timestamp, cases)

class Skipped(Bin):
    norun: bool

    # FIXME: Put norun last in signature.
    def __init__(self, name: str, norun: bool, suites: List[SkippedSuite]):
        super().__init__(name, suites)

        assert isinstance(norun, bool)
        self.norun = norun

    def is_not_run(self):
        return self.norun

    def filter_tests(self, spec: SystemSpec) -> Optional[Self]:
        new_suites = []
        for suite in self.suites:
            s = suite.filter_tests(spec)
            if s is not None:
                new_suites.append(s)
        self.suites = new_suites

        if len(self.suites) != 0:
            return self
        else:
            return None

    @classmethod
    def make_from_dict(cls, skipped: dict) -> Self:
        """
        Create obj from the format:
        {
            'name': name
            'norun': norun
            'suites': [ %SkippedSuite% ]
        }
        """
        name = skipped['name']
        norun = skipped.get('norun', False)
        suites = [SkippedSuite.make_from_dict(suite)
                  for suite in skipped.get('suites', ())]
        return cls(name, norun, suites)
