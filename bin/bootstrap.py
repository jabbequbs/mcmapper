#!/usr/bin/env python3

import glob
import os
import subprocess
import sys

def main():
    pattern = os.path.join(os.path.dirname(sys.executable), "*._pth")
    filenames = glob.glob(pattern)
    if len(filenames) == 1:
        with open(filenames[0], "a") as f:
            f.write("\nimport site\n")
    if os.path.isfile("get-pip.py"):
        subprocess.Popen([sys.executable, "get-pip.py"]).wait()
    if os.path.isfile("requirements.txt"):
        subprocess.Popen([sys.executable] + "-m pip install -r requirements.txt".split()).wait()

if __name__ == '__main__':
    main()
