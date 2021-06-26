#!/usr/bin/env python3

import os
import subprocess

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    if not os.path.isdir("python3"):
        subprocess.call([sys.executable, "-m", "venv", "python3"])
        venvPy = next(os.path.abspath(p)
            for p in ("python3/bin/python3", "python3/Scripts/python.exe")
            if os.path.isfile(os.path.abspath(p)))
        subprocess.call([venvPy, "-m", "pip", "install",
            os.path.join("scripts", "requirements.txt")])
    venvPy = next(os.path.abspath(p)
        for p in ("python3/bin/python3", "python3/Scripts/python.exe")
        if os.path.isfile(os.path.abspath(p)))
    subprocess.call([venvPy, os.path.join("scripts", "viewer.py")])

if __name__ == '__main__':
    main()
