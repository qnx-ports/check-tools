# check-tools
[![Build](https://github.com/qnx-ports/check-tools/actions/workflows/ubuntu-22.04.yml/badge.svg)](https://github.com/qnx-ports/check-tools/actions/workflows/ubuntu-22.04.yml)

Tools for writing the APKBUILD check() function.

## Project Contents

- `doc`/:         Design documentation, guides, and help.
- `check_utils/`: The python module for writing test log parsers for producing
                  JUnitXML reports.
- `bin/check.py`: Tool for reading package configuration, forwarding arguments
                  to the corresponding test framework, formatting JUnitXML
                  output, and returning the result of the test run.

## Get Started

Clone this repo on the target machine, then run the following from the project
root,

```bash
python3 -m ensurepip
python3 -m pip install check_utils
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
  - [ ] Workflow is verified on QNX.
  - [x] Skipped tests are added to the resulting JUnitXML.
  - [x] Errored tests are added to the resulting JUnitXML.
  - [ ] Can execute a custom number of jobs in parallel.
- catch2:
  - [x] Workflow is implemented.
  - [ ] Workflow is verified on linux.
  - [ ] Workflow is verified on QNX.
  - [ ] Skipped tests are added to the resulting JUnitXML.
  - [ ] Errored tests are added to the resulting JUnitXML.
  - [ ] Can execute a custom number of jobs in parallel.
- meson:
  - [x] Workflow is implemented.
  - [ ] Workflow is verified on linux.
  - [ ] Workflow is verified on QNX.
  - [ ] Skipped tests are added to the resulting JUnitXML.
  - [ ] Errored tests are added to the resulting JUnitXML.
  - [ ] Can execute a custom number of jobs in parallel.
- pytest:
  - [x] Workflow is implemented.
  - [ ] Workflow is verified on linux.
  - [ ] Workflow is verified on QNX.
  - [ ] Skipped tests are added to the resulting JUnitXML.
  - [ ] Errored tests are added to the resulting JUnitXML.
  - [ ] Can execute a custom number of jobs in parallel.
