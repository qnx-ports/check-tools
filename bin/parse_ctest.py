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

config_obj = cu.Config.make_config()

Path(config_obj['out_dir']).mkdir(parents=True, exist_ok=True)

# Ctest reports don't output results per case.
# FIXME: Need to be able to detect errors or skipped tests.
case_pattern = r'^\s*[0-9]+\/[0-9]+\s+(Test\s+#[0-9]+:\s+[0-9a-zA-Z_\/\.\-]*)\s+\.+\**\s*(Passed|Failed)\s+([0-9\.]+)\s+sec'

timestamp = datetime.datetime.now().isoformat()

passed_suites = []
failed_suites = []
errored_suites = []

passed_cases: List[cu.PassedCase] = []
failed_cases: List[cu.FailedCase] = []

skipped_suites = [skipped_obj
                  for skipped_config in config_obj.get('custom', dict()).get('skipped', dict()).get('suites', [])
                  if (skipped_obj := cu.SkippedSuite.make_from_dict(skipped_config).filter_tests(cu.SystemSpec.from_uname())) is not None]

with open(config_obj['out_dir'] + '/' + config_obj['package'] + '.txt', 'w') as out:
    for line in sys.stdin:
        if (match := re.match(case_pattern, line)):
            suite = match.group(1).strip()
            case = suite

            if len([True
                    for skipped_suite in skipped_suites
                    for case_name in skipped_suite.get_case_names()
                    if skipped_suite.get_name() == suite and case_name == suite]) == 0:
                if match.group(2) == 'Passed':
                    passed_suites.append(cu.PassedSuite(suite, '', timestamp, [cu.PassedCase(case, '', match.group(3), '')]))
                else:
                    failed_suites.append(cu.FailedSuite(suite, '', timestamp, [cu.FailedCase(case, '', match.group(3), '', '', '')]))

        out.write(line)

xml_report = cu.JUnitXML.make_from_passed(passed_suites)
xml_report += cu.JUnitXML.make_from_failed(failed_suites)
xml_report += cu.JUnitXML.make_from_errored(errored_suites)
xml_report += cu.JUnitXML.make_from_skipped(skipped_suites)

xml_report.write(Path(config_obj['out_dir']).joinpath(config_obj['package'] + '.xml'))

if xml_report.is_success():
    exit(cu.CheckExit.EXIT_SUCCESS)

exit(cu.CheckExit.EXIT_FAILURE)
