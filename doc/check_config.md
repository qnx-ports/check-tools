# check.py writeup

Run all test cases for a port, excluding skipped tests, then fail the check()
function depending on whether the report contains an unexpected failure or
error.

The idea was that running tests with some skipped on certain platforms, and
appropriately formatting the result, comes with certain complications that
should be abstracted from the porter.

This tool does something similar to
https://github.com/grpc/grpc/blob/master/tools/run_tests/run_tests.py

googletest:
`foo_test --gtest_output="xml:path" --gtest_filter=*-FooTest.Bar:BarTest.*`

pytest:
https://docs.pytest.org/en/latest/how-to/usage.html#specifying-tests-selecting-tests
`pytest -k "MyClass and not method" --junit-xml=path`

Each test file will be run, and the JUnitXML result from the file will be added
to the congregate report.

Should add skipped tests to the congregate report.

NOTE: junitxml reports skipped tests on a test case basis. Will need to get the
list of test cases in order to report a skipped suite, which can run into issues
if the file itself crashes or deadlocks (gRPC comes to mind). We will have to
skip these without otherwise reporting them. See norun.

Should add errored tests to the congregate report when it's not already done
(i.e. for googletest).

Should have a package level test.toml file that applies only to the package,
and a project level test.toml file that applies to all packages containing
preset defaults.

Do we want to skip entire files on an arch or os basis?

```toml
# test.toml

package = "name"
timeout = 1800 # Timeout per test file in seconds
# Prefer not to modify. Set to startdir by default.
out_dir = "."

# Frameworks abstracted to include those run at project level and those run at
# binary level.
# Rules for each binary test framework
[googletest]
path = "build" # path to folder containing tests

[[googletest.opts]]
name = "common"
opt = "--non-default-option"
[[googletest.opts]]
name = "build/googletest/sample9_unittest"
opt = "--non-default-option"

[[googletest.skipped]]
name = "build/googletest/sample9_unittest"
norun = false # Assumed false.
[[googletest.skipped.suites]]
name = "CustomOutputTest"
file = "googletest/googletest/samples/sample9_unittest.cc" # For reporting in junitxml.
[[googletest.skipped.suites.cases]]
name = "Fails"
line = "90"
os = [
    "7.1.0", # Skip on 7.1.0 targets.
    "8.0.0"
]
arch = [
    "aarch64le",
    "x86_64"
]
[[googletest.skipped.suites.cases]]
name = "Succeeds" # Skip on all targets.
[[googletest.skipped]]
name = "build/googletest/gtest_no_test_unittest"
norun = true # Will not be added to the test report.

# Rules for each project test framework
[pytest]
path = "build" # path to test folder
opt = "--non-default-option" # example '-n 4' for running 4 parallel jobs on different cores
[[pytest.skipped.suites]]
name = "suite1"
[[pytest.skipped.suites.cases]]
name = "case1"
os = [
    "7.1.0", # Skip on 7.1.0 targets.
    "8.0.0"
]
arch = [
    "aarch64le",
    "x86_64"
]
[[pytest.skipped.suites.cases]]
name = "case2" # Skip on all targets.

# Ignored by check.py
# Manually handle test running and all custom parsing, using your own
# configuration.
[custom]
opt = "--non-default-option"
[[custom.skipped]]
name = "case1"
os = [
    "7.1.0", # Skip on 7.1.0 targets.
    "8.0.0"
]
arch = [
    "aarch64le",
    "x86_64"
]
[[custom.skipped]]
name = "case2" # Skip on all targets.
```
