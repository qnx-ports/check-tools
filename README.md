# check-tools
[![Build](https://github.com/qnx-ports/check-tools/actions/workflows/ubuntu-22.04.yml/badge.svg)](https://github.com/qnx-ports/check-tools/actions/workflows/ubuntu-22.04.yml)

Tools for writing the APKBUILD check() function.

## Project Contents

- `doc/`:         Design documentation, guides, and help.
- `check_utils/`: The python module for writing test log parsers for producing
                  JUnitXML reports.
- `cucheck`:      Tool for reading package configuration, forwarding arguments
                  to the corresponding test framework, formatting JUnitXML
                  output, and returning the result of the test run.
- `cuparse_*`:    Scripts for reading package configuration, parsing stdout of
                  a test program, formatting JUnitXML output, and returning
                  the result of the test run.

## Get Started

Clone this repo on the target machine, then run the following from the project
root,

```bash
python3 -m ensurepip
python3 -m pip install -e '.[tests][html]'
export PATH=$PATH:$PWD/bin
```

## Create a Configuration

Create a `test.toml` file containing values to interface with the underlying
test framework(s), i.e.,
```toml
# test.toml

package = "name"
timeout = 1800 # Timeout per test file in seconds
# Prefer not to modify. Set to startdir by default.
out_dir = "."
jobs = 4 # OR ${{nproc}} (Processed as an integer literal, not a string)

# Frameworks abstracted to include those run at project level and those run at
# binary level.
# Rules for each binary test framework
[googletest]
path = """
build/test/*
build/bin/*""" # glob, so we can automatically test new releases.

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
```

## Orchestrate a Test Suite

Run the test suite. If you're testing in `APKBUILD`, `START_DIR` will default to
the `startdir` path.
```bash
START_DIR=<path-to-config-folder> cucheck
```
The result of the test run will be written to `test-out/<packge>.xml`.

## Test the check-tools Project
```bash
pytest
```

## Framework Support

As the self hosted process for QNX is still early in development, support for
many test frameworks still needs to be added.

The current progress for `cucheck`:
- googletest:
  - [x] Workflow is implemented.
  - [x] Workflow is verified on linux.
  - [x] Workflow is verified on QNX.
  - [x] Skipped tests are added to the resulting JUnitXML.
  - [x] Errored tests are added to the resulting JUnitXML.
- catch2:
  - [x] Workflow is implemented.
  - [ ] Workflow is verified on linux.
  - [ ] Workflow is verified on QNX.
  - [ ] Skipped tests are added to the resulting JUnitXML.
  - [ ] Errored tests are added to the resulting JUnitXML.
- qt-test:
  - [x] Workflow is implemented.
  - [x] Workflow is verified on linux.
  - [x] Workflow is verified on QNX.
  - [x] Skipped tests are added to the resulting JUnitXML.
  - [ ] Errored tests are added to the resulting JUnitXML.
- ctest:
  - [x] Workflow is implemented.
  - [x] Workflow is verified on linux.
  - [ ] Workflow is verified on QNX.
  - [x] Skipped tests are added to the resulting JUnitXML.
  - [ ] Errored tests are added to the resulting JUnitXML.
- meson:
  - [x] Workflow is implemented.
  - [x] Workflow is verified on linux.
  - [ ] Workflow is verified on QNX.
  - [x] Skipped tests are added to the resulting JUnitXML.
  - [ ] Errored tests are added to the resulting JUnitXML.
- pytest:
  - [x] Workflow is implemented.
  - [x] Workflow is verified on linux.
  - [x] Workflow is verified on QNX.
  - [x] Skipped tests are added to the resulting JUnitXML.
  - [ ] Errored tests are added to the resulting JUnitXML.
