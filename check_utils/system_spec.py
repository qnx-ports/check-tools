"""
Provides an abstraction for system information used to select tests.
"""

import os
import subprocess

class SystemSpec:
    os = ''
    arch = ''

    def __init__(self, os: str, arch: str):
        self.os = os
        self.arch = arch

    def get_os(self) -> str:
        return self.os

    def get_arch(self) -> str:
        return self.arch

    @classmethod
    def from_uname(cls):
        status, output = subprocess.getstatusoutput('uname -a')
        if not (os.WIFEXITED(status) and (os.WEXITSTATUS(status) == 0)):
            raise subprocess.CalledProcessError('uname command failed.',
                                                cmd='uname -a')

        # uname output has the form sysname, nodename, release, version,
        # machine, arch.
        spec = output.strip().split()
        return cls(spec[2], spec[5])
