# check-tools
[![Build](https://github.com/qnx-ports/check-tools/actions/workflows/ubuntu-22.04.yml/badge.svg)](https://github.com/qnx-ports/check-tools/actions/workflows/ubuntu-22.04.yml)

Tools for writing the APKBUILD check() function.

## Project Contents

- `doc`/:           Design documentation, guides, and help.
- `check_utils/`:   The python module for writing test log parsers for producing
                    JUnitXML reports.
- `bin/check.sh`:   Tool for reading package configuration, forwarding arguments
                    to the corresponding test framework, formatting JUnitXML
                    output, and returning the result of the test run.
- `bin/parse_*.sh`: Scripts for reading package configuration, parsing stdout of
                    a test program, formatting JUnitXML output, and returning
                    the result of the test run.

## Get Started

Clone this repo on the target machine, then run the following from the project
root,

```bash
python3 -m ensurepip
python3 -m pip install -e ./
export PATH=$PATH:$PWD/bin
```

## Run the Tests
```bash
python3 -m pip install -r tests/requirements.txt
pytest
```

## Framework Support

As the self hosted process for QNX is still early in development, support for
many test frameworks still needs to be added.

The current progress for `bin/check.py`:
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
  - [ ] Workflow is verified on linux.
  - [x] Workflow is verified on QNX.
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
