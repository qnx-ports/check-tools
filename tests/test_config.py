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
Unit tests for config.py
"""

import os
import pytest
import subprocess

from check_utils import Config, PROJECT_DIR
import common


def test__preprocess_empty():
    assert Config._preprocess('') == ''

def _get_nproc():
    return subprocess.check_output('nproc',
                                   shell=True).decode('utf-8').strip()


NPROC = _get_nproc()

@pytest.mark.parametrize('toml,translation', [
    (# toml
     'key1 = 4\n'
     'key2 = "foo1"\n'
     'key3 = 5',
     # translation
     'key1 = 4\n'
     'key2 = "foo1"\n'
     'key3 = 5'),
    (# toml
     'key1 = ${{nproc}}\n'
     'key2 = "foo1"\n'
     'key3 = 5',
     # translation
     f'key1 = {NPROC}\n'
     'key2 = "foo1"\n'
     'key3 = 5'),
    (# toml
     'key1 = "foo1"\n'
     'key2 = "${{nproc}}"\n'
     'key3 = 5',
     # translation
     'key1 = "foo1"\n'
     f'key2 = "{NPROC}"\n'
     'key3 = 5'),
    (# toml
     'key1 = 4\n'
     'key2 = "foo1"\n'
     'key3 = ${{project_dir}}',
     # translation
     'key1 = 4\n'
     'key2 = "foo1"\n'
     f'key3 = {PROJECT_DIR}'),
    ])
def test__preprocess(toml, translation):
    out = Config._preprocess(toml)

    assert out == translation
