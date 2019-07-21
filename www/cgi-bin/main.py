#!/usr/bin/env python3

import cgitb
cgitb.enable()

import os
import sys

basepath = os.path.join(os.path.dirname(__file__), "..", "..", "bin")
sys.path.extend((
    os.path.join(basepath, "lib"),
    os.path.join(basepath, "cgi"),
    ))

import cgibase

if __name__ == '__main__':
    cgibase.main()
