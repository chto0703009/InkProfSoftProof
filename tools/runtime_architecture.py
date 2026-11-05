# Copyright (c) 2026 Christer Törnkvist <christer@borgasundsfotografiska.se>
# SPDX-License-Identifier: GPL-3.0-or-later
"""Detect the current Python process and Mac CPU, including Rosetta.

The translation flag must be queried inside this process, not by launching a
sysctl subprocess: that subprocess might use a different architecture.
Apple: developer.apple.com/documentation/apple-silicon/about-the-rosetta-translation-environment
"""
import ctypes
import json
import platform


def sysctl_int(name):
    try:
        libc = ctypes.CDLL(None, use_errno=True)
        query = libc.sysctlbyname
        query.argtypes = [ctypes.c_char_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t), ctypes.c_void_p, ctypes.c_size_t]
        query.restype = ctypes.c_int
        value = ctypes.c_int()
        size = ctypes.c_size_t(ctypes.sizeof(value))
        if query(name.encode('ascii'), ctypes.byref(value), ctypes.byref(size), None, 0) == 0:
            return value.value
    except (OSError, AttributeError):
        pass
    return None


def detect_runtime(machine=None, query=None):
    machine = (machine or platform.machine()).lower()
    process = {'aarch64': 'arm64', 'amd64': 'x86_64'}.get(machine, machine)
    query = query or sysctl_int
    translated = query('sysctl.proc_translated')
    arm_hardware = query('hw.optional.arm64')
    if translated == 1:
        hardware, execution = 'Apple Silicon', 'rosetta'
    elif process == 'arm64':
        hardware, execution = 'Apple Silicon', 'native'
    elif process == 'x86_64' and arm_hardware == 0:
        hardware, execution = 'Intel', 'native'
    elif arm_hardware == 1:
        hardware, execution = 'Apple Silicon', 'unknown'
    else:
        hardware, execution = 'unknown', 'unknown'
    return dict(hardware=hardware, process=process, execution=execution)


if __name__ == '__main__':
    print(json.dumps(detect_runtime(), indent=2))
