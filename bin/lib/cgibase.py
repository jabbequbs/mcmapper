#! /usr/bin/env python3

import importlib
import logging
import os
import sys
import wsgibase

from traceback import format_exc
from wsgiref.handlers import CGIHandler
from wsgiref.util import shift_path_info

def main():
    basepath = os.path.dirname(__file__)

    logging.basicConfig(
        filename=os.path.join(basepath, "..", "logs", "cgi.log"),
        # filemode="w",
        format="[%(asctime)s] - %(module)s.%(levelname)s - %(message)s",
        level=logging.INFO)

    try:
        scriptName = shift_path_info(os.environ)
        script = importlib.import_module(scriptName)
        os.chdir(os.path.dirname(script.__file__))
        CGIHandler().run(wsgibase.ErrorCatcher(script.app))
    except Exception as e:
        details = format_exc().strip()
        logging.error(str(e) + "\n" + details)
        print("Content-Type: text/plain")
        print()
        print(details)
