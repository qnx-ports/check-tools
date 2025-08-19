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
Run tests from APKBUILD check() function given a test configuration file.
Output results in JUnitXML.
"""

import argparse
import datetime
#from functools import cache
import logging
from pathlib import Path
import sys
from typing import Generator

import check_utils

class Main:
    """
    Entrypoint to the program.
    """
    verbose: int = 0

    start_time: str = ''
    # Get package name from cwd if none is provided.
    # Get tmp dir from os.getenv if none is provided.
    config_obj: check_utils.Config = None

    def __init__(self, config: str, project_config: str, verbose: int) -> None:
        """
        Initialize Main.

        @param config: Name of the config file.
        @param verbose: Verbosity level.
        """
        self.config_obj = check_utils.Config.make_config(config, project_config)

        self.verbose = verbose

    # --- PRIVATE ---
    def _generate_outfile_name(self, *args: str, extension: str) -> str:
        """
        Generates the name of a report.

        @param package: Name of the package.
        @param extension: File extension to use.
        @param binary: Name of the test file, if any.
        @return generated report name.
        """
        if extension[0] != '.':
            extension = '.' + extension
        return '_'.join(args) + extension

    def _generate_test_jobsets(
            self,
            output: str
            ) -> Generator[check_utils.TestJobset, None, None]:
        """
        Generate all tests to run.

        @param output: name of the command-line output file.
        @yield a test to run.
        """
        spec = check_utils.SystemSpec.from_uname()
        for test_framework in check_utils.TEST_FRAMEWORK_BUILTINS:
            jobset = test_framework.make_test_jobset(
                    output,
                    spec,
                    self.config_obj
                    )
            if jobset is not None:
                yield jobset

    # --- PUBLIC ---
    def is_success(self, report: str) -> bool:
        """
        Check if testing succeeded based on the generated report.

        @return True if there were no failures or errors,
                False otherwise.
        """
        return check_utils.JUnitXML(report).is_success()

    def setup(self) -> None:
        """
        Setup a run of the program.
        """
        if self.verbose == 0:
            logging.basicConfig(stream=sys.stdout, level=logging.ERROR)
        elif self.verbose == 1:
            logging.basicConfig(stream=sys.stdout, level=logging.WARN)
        elif self.verbose == 2:
            logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
        else:
            raise check_utils.IllegalArgumentError("Supplied invalid "
                                                   "verbosity.")

        self.start_time = datetime.datetime.now().isoformat()

        Path(self.config_obj['out_dir']).mkdir(parents=True, exist_ok=True)

    def main(self) -> check_utils.CheckExit:
        """
        Entrypoint for the program.
        """
        self.setup()

        report: str = self.config_obj['out_dir'] + '/' \
                + self._generate_outfile_name(
                        self.config_obj['package'],
                        extension='.xml'
                        )
        output: str = self.config_obj['out_dir'] + '/' \
                + self._generate_outfile_name(
                        self.config_obj['package'],
                        extension='.txt'
                        )
        num_jobs: int = self.config_obj.get('jobs', 1)
        logging.info('Reporting results in %s.', report)
        logging.info('Reporting output in %s.', output)
        logging.info('Using %d jobs.', num_jobs)

        combined_report_obj = check_utils.JUnitXML.make_from_passed([])
        is_empty = True
        for test in self._generate_test_jobsets(output):
            is_empty = False
            combined_report_obj += test.run(num_jobs)

        combined_report_obj.write(report)

        if is_empty:
            logging.warning("No tests were run!")
            return check_utils.CheckExit.EXIT_SUCCESS

        if self.is_success(report):
            return check_utils.CheckExit.EXIT_SUCCESS

        return check_utils.CheckExit.EXIT_FAILURE

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
            prog='check.py',
            description='Runs tests for a package.',
            )

    parser.add_argument(
            '-c', '--config',
            type=str,
            default=check_utils.PACKAGE_CONFIG,
            help='Package-level configuration file.',
            )
    parser.add_argument(
            '-p', '--project-config',
            type=str,
            default=check_utils.PROJECT_CONFIG,
            help="Project-level configuration file. Takes its value from "
            "`os.getenv('PROJECT_CONFIG')` by default",
            )
    parser.add_argument(
            '-v', '--verbose',
            action='count',
            default=0,
            help='Verbose output. Maximum value of 2.'
            )
    args = parser.parse_args()

    m = Main(args.config, args.project_config, args.verbose)
    sys.exit(m.main())
