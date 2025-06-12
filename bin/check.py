"""
Run tests from APKBUILD check() function given a test configuration file.
Output results in JUnitXML.
"""

import argparse
import datetime
#from functools import cache
import logging
import os
from pathlib import Path
import sys
import tempfile
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
        return '_'.join(args) + self.start_time + extension

    def _combine_congregate_report(self, congregate_report: str,
                                   individual_report: str) -> None:
        """
        Combines the report result of an individual test into the congregate
        report. Unlinks the individual report.

        @param congregate_report: The congregate report.
        @param individual_report: The report result of an individual test.
        @raise check_utils.IllegalArgumentError: Provided an illegal argument.
        """
        if not Path(individual_report).exists()\
                and Path(individual_report).is_file():
            logging.error('%s does not exist!', individual_report)
            raise check_utils.IllegalArgumentError('combine_congregate_report()'
                                                   ' given path to empty '
                                                   'JUnitXML file.')
        if (congregate_report is not None) and Path(congregate_report).exists()\
                and Path(congregate_report).is_file():
            logging.info('Combining %s with result %s.',
                             congregate_report, individual_report)

            congregate_xml = check_utils.JUnitXML(congregate_report)

            individual_xml = check_utils.JUnitXML(individual_report)

            congregate_xml += individual_xml
            congregate_xml.write(congregate_report)

            # Cleanup temporary files.
            Path(individual_report).unlink()
        else:
            logging.info('Renaming %s to %s.', individual_report,
                             congregate_report)
            Path(individual_report).rename(congregate_report)

    def _generate_test_list(
            self,
            output: str
            ) -> Generator[check_utils.GenericTest, None, None]:
        """
        Generate all tests to run.

        @param output: name of the command-line output file.
        @yield a test to run.
        """
        def _report_f(binary):
            f, tmp_report = tempfile.mkstemp(suffix='.xml')
            os.close(f)
            return tmp_report

        spec = check_utils.SystemSpec.from_uname()
        for test_framework in check_utils.TEST_FRAMEWORK_BUILTINS:
            # We don't want to keep any generated reports, so provide a temp
            # file instead.
            yield from test_framework.generate_test_list(
                    output,
                    spec,
                    self.config_obj,
                    _report_f
                    )

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
        logging.info('Reporting results in %s.', report)
        logging.info('Reporting output in %s.', output)

        is_empty = True
        for test in self._generate_test_list(output):
            is_empty = False
            test.run()
            self._combine_congregate_report(congregate_report = report,
                                            individual_report = test.get_report())

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
            help='Verbose output. Maximum value of 3.'
            )
    args = parser.parse_args()

    m = Main(args.config, args.project_config, args.verbose)
    sys.exit(m.main())
