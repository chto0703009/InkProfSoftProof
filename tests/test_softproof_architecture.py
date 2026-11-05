# Copyright (c) 2026 Christer Törnkvist <christer@borgasundsfotografiska.se>
# SPDX-License-Identifier: GPL-3.0-or-later
"""Architecture detection without relying on the test machine's CPU."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from runtime_architecture import detect_runtime


class ArchitectureTests(unittest.TestCase):
    def detect(self, machine, translated, arm):
        flags = {'sysctl.proc_translated': translated, 'hw.optional.arm64': arm}
        return detect_runtime(machine, flags.get)

    def test_native_arm(self):
        self.assertEqual(self.detect('arm64', 0, 1), dict(hardware='Apple Silicon', process='arm64', execution='native'))

    def test_native_intel(self):
        self.assertEqual(self.detect('x86_64', None, 0), dict(hardware='Intel', process='x86_64', execution='native'))

    def test_rosetta_is_apple_silicon_hardware(self):
        self.assertEqual(self.detect('x86_64', 1, 0), dict(hardware='Apple Silicon', process='x86_64', execution='rosetta'))

    def test_unavailable_queries_do_not_claim_native_intel(self):
        self.assertEqual(self.detect('x86_64', None, None)['execution'], 'unknown')
        self.assertEqual(self.detect('x86_64', None, None)['hardware'], 'unknown')

    def test_native_arm_does_not_require_translation_flag(self):
        self.assertEqual(self.detect('arm64', None, None)['execution'], 'native')

    def test_contradictory_flags_remain_unknown(self):
        self.assertEqual(self.detect('x86_64', 0, 1)['execution'], 'unknown')


if __name__ == '__main__': unittest.main()
