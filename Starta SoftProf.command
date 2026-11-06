#!/bin/sh
set -eu
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
    echo 'SoftProfs Python-miljö saknas. Kör projektets miljöinstallation först.'
    exit 1
fi
exec .venv/bin/python tools/launch_softproof.py
