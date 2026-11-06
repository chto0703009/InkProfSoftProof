#!/usr/bin/env python3
# Copyright (c) 2026 Christer Törnkvist <christer@borgasundsfotografiska.se>
# SPDX-License-Identifier: GPL-3.0-or-later
"""Fail if any Mach-O file in an app contains the wrong CPU architecture."""
import argparse
import hashlib
import json
import plistlib
import re
from pathlib import Path
import subprocess
from runtime_architecture import detect_runtime

MAGIC = {bytes.fromhex(value) for value in ('feedface','cefaedfe','feedfacf','cffaedfe','cafebabe','bebafeca','cafebabf','bfbafeca')}


def native_tool(name):
    # A translated Intel build process must not invoke Intel xcrun against an
    # ARM-only Command Line Tools installation on the build host.
    runtime = detect_runtime()
    prefix = ['/usr/bin/arch','-arm64'] if runtime['execution']=='rosetta' else []
    return prefix+['/usr/bin/'+name]


def version_tuple(value):
    parts=tuple(map(int,value.split('.')))
    return parts+(0,)*(3-len(parts))


def minimum_macos(commands):
    values=re.findall(r'\bminos\s+([\d.]+)',commands)
    values+=re.findall(r'cmd LC_VERSION_MIN_MACOSX\s+cmdsize \d+\s+version ([\d.]+)',commands)
    return max(values,key=version_tuple) if values else None


def audit(app, expected):
    app = Path(app).resolve(); seen=set(); files=[]
    declared=plistlib.loads((app/'Contents/Info.plist').read_bytes())['LSMinimumSystemVersion']
    for path in sorted(app.rglob('*')):
        if path.is_symlink() and not path.resolve().is_relative_to(app):
            raise ValueError(f'External app symlink: {path}')
        if not path.is_file() or path.resolve() in seen: continue
        seen.add(path.resolve())
        with path.open('rb') as stream: magic=stream.read(4)
        if magic not in MAGIC: continue
        architectures=subprocess.check_output(native_tool('lipo')+['-archs',str(path)],text=True).split()
        if architectures != [expected]:
            raise ValueError(f'{path.relative_to(app)}: {architectures}, expected only {expected}')
        commands=subprocess.check_output(native_tool('otool')+['-l',str(path)],text=True)
        minimum=minimum_macos(commands)
        if minimum is None: raise ValueError(f'Missing minimum macOS version: {path.relative_to(app)}')
        if version_tuple(minimum)>version_tuple(declared):
            raise ValueError(f'{path.relative_to(app)} requires macOS {minimum}, app declares {declared}')
        files.append(dict(path=str(path.relative_to(app)),architecture=expected,minimum_macos=minimum,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    if not files: raise ValueError('No Mach-O files found in app')
    return dict(app=app.name,architecture=expected,minimum_macos=declared,binary_minimum_macos=max((f['minimum_macos'] for f in files),key=version_tuple),binary_count=len(files),files=files)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('app');parser.add_argument('--arch',choices=['arm64','x86_64'],required=True)
    args=parser.parse_args();print(json.dumps(audit(args.app,args.arch),indent=2))
