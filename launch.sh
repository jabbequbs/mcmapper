#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd $DIR
if [ ! -d "python3" ]; then
    python3 -m venv python3
    . python3/bin/activate
    pip install -r scripts/requirements.txt
    deactivate
fi
. python3/bin/activate
python3 scripts/viewer.py
