"""
Provides data formats for skipped tests to help communicate with the underlying
test framework, and convert to JUnitXML.
"""

from typing import List, Optional, Self

from .system_spec import SystemSpec

class SkippedCase:
    name: str = ''
    line: str = ''
    os: List[str] = []
    arch: List[str] = []
    message: Optional[str] = None

    def __init__(self, name: str, line: str, os: List[str], arch: List[str],
                 message: Optional[str] = None):
        assert isinstance(name, str)
        assert isinstance(line, str)
        assert isinstance(os, list)
        assert isinstance(arch, list)
        self.name = name
        self.line = line
        self.os = os
        self.arch = arch
        self.message = message

    def get_name(self) -> str:
        return self.name

    def get_line(self) -> str:
        return self.line

    def get_os(self) -> List[str]:
        return self.os

    def get_arch(self) -> List[str]:
        return self.arch

    def get_message(self) -> str:
        if self.message is not None:
            return self.message

        return 'Skipped for '\
               + ('/'.join(self.os) if len(self.os) != 0 else 'all SDPs')\
               + ' on '\
               + ('/'.join(self.arch) if len(self.arch) != 0 else 'all archs')\
               + '.'

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

class SkippedSuite:
    name: str = ''
    file: str = ''
    timestamp: str = ''
    cases: List[SkippedCase]

    def __init__(self, name: str, file: str, timestamp: str,
                 cases: List[SkippedCase]):
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

class Skipped:
    name: str = ''
    norun: bool = False
    suites: List[SkippedSuite] = []

    def __init__(self, name: str, norun: bool, suites: List[SkippedSuite]):
        assert isinstance(name, str)
        assert isinstance(norun, bool)
        assert isinstance(suites, list)
        self.name = name
        self.norun = norun
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

    def is_not_run(self):
        return self.norun

    def get_suites(self):
        return self.suites

    def is_empty(self):
        if self.suites is not None:
            for suite in self.suites:
                if len(suite.get_cases()) != 0:
                    return False
        return True

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
