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

import datetime
from pathlib import Path
import re
import sys
from typing import List

import check_utils as cu


def main():
    config_obj = cu.Config.make_config()

    Path(config_obj['out_dir']).mkdir(parents=True, exist_ok=True)

    # Suite names are non-standard and will need to be handled on a case-by-case
    # basis.
    # https://node-tap.org/tap-format/
    # By default, use the suite name 'test', otherwise assume that we're parsing
    # prove.
    suite_pattern = r'^([0-9a-zA-Z_\/\.\-]+) \.\.\.+'
    # Sometimes there will be a trailing "ok" to indicate that the entire file
    # succeeded. We will just ignore those.
    # This means that we drop tests that are skipped within the context of TAP.
    length_pattern = r'^([0-9]+)\.\.([0-9]+)'
    case_pattern = r'^(ok|not ok)(?: [0-9]+ \- )?(.*)'
    # Errors are non-standard and will need to be handled on a case-by-case basis.
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
                      for skipped_config in config_obj.get('custom', dict()).get('skipped', dict()).get('suites', [])
                      if (skipped_obj := cu.SkippedSuite.make_from_dict(skipped_config).filter_tests(cu.SystemSpec.from_uname())) is not None]

    suite = None
    length = None
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
                    length = None

                suite = match.group(1).strip()
            elif (match := re.match(length_pattern, line)):
                start = int(match.group(1).strip())
                end = int(match.group(2).strip())
                length = end - start + 1
            elif (match := re.match(case_pattern, line)):
                status = match.group(1).strip()
                case = match.group(2).strip()

                if len([True
                        for skipped_suite in skipped_suites
                        for case_name in skipped_suite.get_case_names()
                        if skipped_suite.get_name() == suite and case_name == case]) != 0 \
                                or ((len(passed_cases) + len(failed_cases)) >= length):
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

    if suite is None:
        suite = 'test'

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


if __name__ == '__main__':
    main()
