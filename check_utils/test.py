"""
Provides common base class definitions for creating test runner objects.
"""

from abc import ABC, abstractmethod
import glob
import logging
from pathlib import Path
from typing import List, Optional, Callable, Generator

from .config import Config
from .skipped import Skipped, SkippedSuite
from .system_spec import SystemSpec

class GenericTest(ABC):
    """
    Abstract class for a runnable test which produces a report file and
    command-line output file.
    """
    report: str = ''
    output: str = ''

    def __init__(self, report, output):
        self.report = report
        self.output = output

    # --- PRIVATE ---
    @abstractmethod
    def _run_impl(self) -> str:
        """
        Run the impl object.

        @raise NotImplementedError: Called an abstract method.
        """
        raise NotImplementedError('_run_impl() not implemented!')

    def _report_skipped_tests(self) -> None:
        """
        Add skipped tests to the report if applicable.
        """
        pass

    def _report_errored_tests(self) -> None:
        """
        Add errored tests to the report if applicable.
        """
        pass

    # --- PUBLIC ---
    def run(self) -> None:
        """
        Run the tests and report the outcome.
        """
        self._run_impl()
        self._report_skipped_tests()
        self._report_errored_tests()

    def get_report(self) -> str:
        """
        Get the name of the report.

        @return report name.
        """
        return self.report

    def get_output(self) -> str:
        """
        Get the name of the command-line output file.

        @return command-line output file name.
        """
        return self.output

class TestGenerator(ABC):
    """
    Abstract class for a factory which produces test instances of the derived
    class.
    """
    # --- PUBLIC ---
    @classmethod
    @abstractmethod
    def generate_test_list(
            cls,
            output: str,
            spec: SystemSpec,
            config: Config,
            report_f: Callable[[str], str]
            ) -> Generator[GenericTest, None, None]:
        """
        Generate test instances.

        @yield a test instance.
        @raise NotImplementedError: Called an abstract method.
        """
        raise NotImplementedError('generate_test_list() not implemented!')

    @classmethod
    @abstractmethod
    def get_name_framework(cls) -> str:
        """
        Get the name of the test framework this class represents.

        @return the name of the framework.
        @raise NotImplementedError: Called an abstract method.
        """
        raise NotImplementedError('get_name_framework() not implemented!')

class BinaryTest(GenericTest, TestGenerator, ABC):
    """
    Abstract class for a factory which produces test instances of the derived
    class which correspond to a single executable binary file.
    """
    binary: str = ''
    opts: str = ''
    skipped: Optional[Skipped] = []
    timeout: Optional[int] = None

    def __init__(self, binary: str,
                 report: str, output: str, opts: str,
                 skipped: Optional[Skipped], timeout: Optional[int] = None):
        super().__init__(report, output)
        self.binary = binary
        self.opts = opts
        self.skipped = skipped
        self.timeout = timeout

    # --- PUBLIC ---
    @classmethod
    def generate_test_list(
            cls,
            output: str,
            spec: SystemSpec,
            config: Config,
            report_f: Callable[[str], str]
            ) -> Generator[GenericTest, None, None]:
        logging.info('Generating binary test list for %s.',
                     cls.get_name_framework())
        framework_config = config.get(cls.get_name_framework(), None)
        if framework_config is not None:
            binaries = []
            for path in framework_config.get('path', '').splitlines():
                binaries.extend(p for p in glob.glob(path) if p not in binaries)
            for binary in binaries:
                # Skiplist
                norun = False
                skipped: Optional[Skipped] = None
                for skip_iter in framework_config.get('skipped', []):
                    skip_obj: Skipped = Skipped.make_from_dict(skip_iter)
                    if Path(skip_obj.get_name()) == Path(binary):
                        if skip_obj.is_not_run():
                            # Test is not run.
                            norun = True
                            break
                        skipped = skip_obj.filter_tests(spec)
                if norun:
                    logging.info('Skipping binary %s.', binary)
                    continue

                # Custom options
                common_opts: str = ''
                binary_opts: str = ''
                for opt_iter in framework_config.get('opt', []):
                    if opt_iter['name'] == 'common':
                        common_opts = opt_iter['opt']
                    elif Path(opt_iter['name']) == Path(binary):
                        binary_opts = opt_iter['opt']
                opts = f'{common_opts} {binary_opts}'

                report = report_f(Path(binary).name)

                yield cls(binary, report, output, opts, skipped,
                          config.get('timeout', None))
        else:
            logging.info('Could not find configuration for framework %s.',
                         cls.get_name_framework())

class ProjectTest(GenericTest, TestGenerator, ABC):
    """
    Abstract class for a factory which produces test instances of the derived
    class which correspond to a project-level test runner.
    """
    opts: str = ''
    skipped: List[SkippedSuite] = []
    timeout: Optional[int] = None

    def __init__(self,
                 report: str, output: str, opts: str,
                 skipped: List[SkippedSuite], timeout: Optional[int] = None):
        super().__init__(report, output)
        self.opts = opts
        self.skipped = skipped
        self.timeout = timeout

    # --- PUBLIC ---
    @classmethod
    def generate_test_list(
            cls,
            output: str,
            spec: SystemSpec,
            config: Config,
            report_f: Callable[[str], str]
            ) -> Generator[GenericTest, None, None]:
        logging.info('Generating project test list for %s.',
                     cls.get_name_framework())
        framework_config = config.get(cls.get_name_framework(), None)
        if framework_config is not None:
            skipped = framework_config.get('skipped', [])
            skipped_suites = []
            for suite in skipped.get('suites', []):
                skipped_suite = SkippedSuite.make_from_dict(suite)\
                        .filter_tests(spec)
                if skipped_suite is not None:
                    skipped_suites.append(skipped_suite)

            opts = framework_config.get('opt', '')

            report = report_f('')

            yield cls(report, output, opts, skipped_suites,
                      config.get('timeout', None))
        else:
            logging.info('Could not find configuration for framework %s.',
                         cls.get_name_framework())
