#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd $DIR
if [ ! -d "python3" ]; then
    python3 -m venv python3
    ./python3/bin/python3 -m pip install -r scripts/requirements.txt
fi
./python3/bin/python3 scripts/viewer.py
