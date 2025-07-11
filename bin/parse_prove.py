import datetime
from pathlib import Path
import re
import sys
from typing import List

import check_utils as cu

config_obj = cu.Config.make_config()

Path(config_obj['out_dir']).mkdir(parents=True, exist_ok=True)

suite_pattern = r'^([0-9a-zA-Z_\/\.\-]+) \.+'
case_pattern = r'^(ok|not ok) [0-9]+ \- (.*)'
# Prove reports don't have a clear indication that an error occured until you
# reach the test summary.
e_pattern = r'^([0-9a-zA-Z_\/\.\-]+)\s*\(Wstat: [0-9]+ \(Signal: (.*)\) Tests: [0-9]+ Failed: [0-9]+\)'

timestamp = datetime.datetime.now().isoformat()

passed_suites = []
failed_suites = []
errored_suites = []

passed_cases: List[cu.PassedCase] = []
failed_cases: List[cu.FailedCase] = []

skipped_suites = [skipped_obj
                  for skipped_config in config_obj['custom']['skipped']['suites']
                  if (skipped_obj := cu.SkippedSuite.make_from_dict(skipped_config).filter_tests(cu.SystemSpec.from_uname())) is not None]

suite = None
with open(config_obj['out_dir'] + '/' + config_obj['package'] + '.txt', 'w') as out:
    for line in sys.stdin:
        if (match := re.match(suite_pattern, line)):
            if suite is not None:
                if len(passed_cases) != 0:
                    passed_suites.append(cu.PassedSuite(suite, '', timestamp, passed_cases))
                if len(failed_cases) != 0:
                    failed_suites.append(cu.FailedSuite(suite, '', timestamp, failed_cases))

                passed_cases = []
                failed_cases = []

            suite = match.group(1).strip()
        elif suite is not None and (match := re.match(case_pattern, line)):
            status = match.group(1).strip()
            case = match.group(2).strip()

            if len([True
                    for skipped_suite in skipped_suites
                    for case_name in skipped_suite.get_case_names()
                    if skipped_suite.get_name() == suite and case_name == case]) != 0:
                pass
            elif status == 'ok':
                passed_cases.append(cu.PassedCase(case, '', '', ''))
            else:
                failed_cases.append(cu.FailedCase(case, '', '', '', '', ''))
        elif (match := re.match(e_pattern, line)):
            esuite = match.group(1)
            message = match.group(2)

            if len([True
                    for skipped_suite in skipped_suites
                    for case_name in skipped_suite.get_case_names()
                    if skipped_suite.get_name() == esuite and case_name == esuite]) == 0:
                errored_suites.append(cu.ErroredSuite(esuite, '', timestamp, [cu.ErroredCase(esuite, '', '', '', message, '')]))

        out.write(line)

if suite is not None:
    if len(passed_cases) != 0:
        passed_suites.append(cu.PassedSuite(suite, '', timestamp, passed_cases))
    if len(failed_cases) != 0:
        failed_suites.append(cu.FailedSuite(suite, '', timestamp, failed_cases))

xml_report = cu.JUnitXML.make_from_passed(passed_suites)
xml_report += cu.JUnitXML.make_from_failed(failed_suites)
xml_report += cu.JUnitXML.make_from_errored(errored_suites)
xml_report += cu.JUnitXML.make_from_skipped(skipped_suites)

xml_report.write(Path(config_obj['out_dir']).joinpath(config_obj['package'] + '.xml'))

if xml_report.is_success():
    exit(cu.CheckExit.EXIT_SUCCESS)

exit(cu.CheckExit.EXIT_FAILURE)
