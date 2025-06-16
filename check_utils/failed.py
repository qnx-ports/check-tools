"""
Provides data formats for failed tests to help convert to JUnitXML.
"""
from typing import Self, List

class FailedCase:
    name: str = ''
    line: str = ''
    time: str = '0.0'
    assertions: str = '0'
    message: str = ''
    ftype: str = ''

    def __init__(self, name: str, line: str, time: str,
                 assertions: str, message: str, ftype: str) -> None:
        self.name = name
        self.line = line
        self.time = time
        self.assertions = assertions
        self.message = message
        self.ftype = ftype

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

class FailedSuite:
    name: str = ''
    file: str = ''
    timestamp: str = ''
    cases: List[FailedCase] = []

    def __init__(self, name: str, file: str, timestamp: str,
                 cases: List[FailedCase]) -> None:
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
        cases = [FailedSuite.make_from_dict(case) for case in suite.get('cases', ())]
        return cls(name, file, timestamp, cases)
