# Copyright (c) 2026 Christer Törnkvist <christer@borgasundsfotografiska.se>
# SPDX-License-Identifier: GPL-3.0-or-later
"""Architecture detection without relying on the test machine's CPU."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from runtime_architecture import detect_runtime
from audit_softproof_architecture import minimum_macos, version_tuple


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


class DeploymentTests(unittest.TestCase):
    def test_modern_and_legacy_binary_targets(self):
        modern='cmd LC_BUILD_VERSION\n cmdsize 32\n platform 1\n minos 13.0\n sdk 27.0'
        legacy='cmd LC_VERSION_MIN_MACOSX\n cmdsize 16\n version 10.13\n sdk 10.15'
        self.assertEqual(minimum_macos(modern),'13.0')
        self.assertEqual(minimum_macos(legacy),'10.13')
        self.assertEqual(minimum_macos(legacy+'\n'+modern),'13.0')
        self.assertIsNone(minimum_macos('Not a load command'))

    def test_deployment_comparison_is_numeric(self):
        self.assertLess(version_tuple('10.9'),version_tuple('10.13'))
        self.assertEqual(version_tuple('13'),version_tuple('13.0.0'))


if __name__ == '__main__': unittest.main()
