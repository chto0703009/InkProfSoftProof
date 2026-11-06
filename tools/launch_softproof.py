#!/usr/bin/env python3
# Copyright (c) 2026 Christer Törnkvist <christer@borgasundsfotografiska.se>
# SPDX-License-Identifier: GPL-3.0-or-later
"""Prepare and open the local Python macOS app; no Swift compiler required."""
import argparse
import os
from pathlib import Path
import plistlib
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT/'local-config/softproof-python/vendor'
APP = ROOT/'local-config/softproof/SoftProf.app'


def prepare():
    sys.path.insert(0, str(VENDOR))
    try:
        import AppKit  # noqa: F401
        import Quartz  # noqa: F401
    except ImportError:
        VENDOR.mkdir(parents=True, exist_ok=True)
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--target', str(VENDOR), '-r', str(ROOT/'tools/requirements-softproof.txt')], check=True)
    macos = APP/'Contents/MacOS'
    macos.mkdir(parents=True, exist_ok=True)
    # Use a relative project location so moving the project does not break the
    # existing app. The project environment supplies the Python interpreter.
    launcher = '''#!/bin/sh
set -eu
project_dir="$(CDPATH= cd -- "$(dirname "$0")/../../../../.." && pwd)"
exec "$project_dir/.venv/bin/python" "$project_dir/tools/softproof_app.py" "$@"
'''
    # Atomic replacement also permits an older, still running Swift app.
    fd, staging = tempfile.mkstemp(dir=macos, prefix='.python-launcher-')
    with os.fdopen(fd, 'w') as stream: stream.write(launcher)
    os.chmod(staging, 0o755); os.replace(staging, macos/'SoftProf')
    info = dict(CFBundleExecutable='SoftProf', CFBundleIdentifier='se.inkprof.softproof', CFBundleName='SoftProf',
                CFBundleDisplayName='SoftProf', CFBundlePackageType='APPL', CFBundleVersion=(ROOT/'VERSION').read_text().strip(), CFBundleShortVersionString=(ROOT/'VERSION').read_text().strip(), NSHumanReadableCopyright='Copyright (c) 2026 Christer Törnkvist <christer@borgasundsfotografiska.se>. GPL-3.0-or-later.',
                NSHighResolutionCapable=True, LSMinimumSystemVersion='13.0')
    (APP/'Contents/Info.plist').write_bytes(plistlib.dumps(info))
    return macos/'SoftProf'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare-only', action='store_true')
    args = parser.parse_args()
    prepare()
    if not args.prepare_only:
        # Start the Python implementation even if the previous Swift version
        # is still running. No active user window or export is terminated.
        subprocess.run(['open', '-n', '-a', str(APP)], check=True)


if __name__ == '__main__': main()
