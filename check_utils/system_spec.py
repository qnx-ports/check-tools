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
Provides an abstraction for system information used to select tests.
"""

import subprocess
import logging

class SystemSpec:
    os: str
    arch: str
    platform: str

    # For qemu, machine can be QEMU_virt or x86pc (on native x86_64).
    # FIXME: Find the equivalent for native aarch64
    # TODO: Test rpi4
    PLATFORM_DEFAULT = 'qemu'
    PLATFORM_NAME_MAPPING = (
            ({'QEMU_virt', 'x86pc'}, 'qemu'),
            ({'RaspberryPi5'}, 'rpi5'),
            ({'RaspberryPi4'}, 'rpi4')
            )

    def __init__(self, os: str, platform: str, arch: str):
        self.os = os
        self.platform = platform
        self.arch = arch

    def get_os(self) -> str:
        return self.os

    def get_arch(self) -> str:
        return self.arch

    def get_platform(self) -> str:
        return self.platform

    @classmethod
    def from_uname(cls):
        status, output = subprocess.getstatusoutput('uname -a')
        if status != 0:
            raise subprocess.CalledProcessError('uname command failed.',
                                                cmd='uname -a')

        # uname output has the form sysname, nodename, release, version,
        # machine, arch.
        spec = output.strip().split()
        machine = spec[4]

        # Get the platform field.
        platform = None
        for machine_vals, mapped_to in cls.PLATFORM_NAME_MAPPING:
            if machine in machine_vals:
                platform = mapped_to
                break

        if platform is None:
            # Assume that we're running on the default.
            platform = cls.PLATFORM_DEFAULT
            logging.warning('Unrecognized machine name %s, assuming platform is'
                            ' %s.', machine, platform)

        return cls(spec[2], platform, spec[5])
