#!/usr/bin/env python3
# Copyright (c) 2026 Christer Törnkvist <christer@borgasundsfotografiska.se>
# SPDX-License-Identifier: GPL-3.0-or-later
"""Fail if any Mach-O file in an app contains the wrong CPU architecture."""
import argparse
import hashlib
import json
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


def audit(app, expected):
    app = Path(app).resolve(); seen=set(); files=[]
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
        files.append(dict(path=str(path.relative_to(app)),architecture=expected,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    if not files: raise ValueError('No Mach-O files found in app')
    return dict(app=app.name,architecture=expected,binary_count=len(files),files=files)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('app');parser.add_argument('--arch',choices=['arm64','x86_64'],required=True)
    args=parser.parse_args();print(json.dumps(audit(args.app,args.arch),indent=2))
