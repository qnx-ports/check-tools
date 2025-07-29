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
Read in test.toml files for a package.
"""

import logging
from pathlib import Path
import tomllib
from typing import Final, Optional, Self

from .definitions import START_DIR, PACKAGE_CONFIG, PROJECT_CONFIG

class Config(dict):
    DEFAULTS: Final[dict] = {
            'out_dir': str(START_DIR.joinpath('test-out'))
            }

    """
    Corresponds to the hierarchical configuration of a package.
    Configuration is read from a aports-level test.toml that applies to all
    packages, and a package-level test.toml file that applies to an individual
    package. The package-level configuration overrides the defaults set in the
    aports-level configuration.
    """
    @classmethod
    def make_config(cls,
                    package_config: Optional[str] = None,
                    project_config: Optional[str] = None) -> Self:
        if package_config is None:
            package_config = PACKAGE_CONFIG
        if project_config is None:
            project_config = PROJECT_CONFIG

        conf = cls.DEFAULTS
        if Path(project_config).exists() and Path(project_config).is_file():
            with open(project_config, "rb") as f:
                temp_conf = tomllib.load(f)
                conf.update(temp_conf)
        else:
            logging.warning('project config %s was not found!', project_config)

        if Path(package_config).exists() and Path(package_config).is_file():
            with open(package_config, "rb") as f:
                temp_conf = tomllib.load(f)
                conf.update(temp_conf)
        else:
            logging.warning('package config %s was not found!', package_config)

        # If neither configuration exists, fallback on KeyError handling...

        return cls(conf)
