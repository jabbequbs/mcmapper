#!/usr/bin/env python3

import argparse
import http.server
import inspect
import logging
import os
import socketserver
import subprocess
import sys
import time
import webbrowser

from urllib.request import urlopen


class LoggingCGIHandler(http.server.CGIHTTPRequestHandler):
    protocol_version = "HTTP/1.0"
    server_version = "LoggingCGIHandler/0.1"

    def log_message(self, fmt, *args):
        logging.info("%s - %s" % (
            self.address_string(),
            fmt%args))

    def log_error(self, fmt, *args):
        message = fmt % args
        if type(message) is bytes:
            try:
                message = message.decode("utf-8")
            except:
                pass
        elif message.startswith("b'"):
            try:
                message = message[2:-1].encode("utf-8").decode("unicode_escape")
                message = "\n".join(message.splitlines())
            except Exception as e:
                logging.error(str(e))
        logging.error("%s - %s" % (
            self.address_string(),
            message))


class Commands(object):
    @staticmethod
    def launch(arglist):
        parser = argparse.ArgumentParser(**Commands._desc)
        parser.add_argument("port", type=int)
        parser.add_argument("--open", action="store_true")
        args = parser.parse_args(arglist)

        print("Starting up...")
        url = "http://localhost:%d/loader.html" % args.port

        # Check if the server is already running
        try:
            server = urlopen(url).info().get("Server")
            expected = LoggingCGIHandler.version_string(LoggingCGIHandler)
            assert server == expected
            # Server is already running, launch the url and exit
            if args.open:
                webbrowser.open(url)
            return
        except Exception as e:
            pass

        # Start the server
        kwargs = {}
        if os.name == "nt":
            CREATE_NO_WINDOW = 0x08000000
            kwargs = {"creationflags": CREATE_NO_WINDOW}
            if sys.executable.lower().endswith("w.exe"):
                sys.executable = sys.executable[:-5]+".exe"

        server = subprocess.Popen(
            [sys.executable, __file__, "serve", str(args.port)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            **kwargs)

        # Wait for the server to start before launching the main page
        for i in range(3):
            time.sleep(1)
            try:
                response = urlopen(url)
                if args.open:
                    webbrowser.open(url)
                print("Server is running (PID = %s)" % server.pid)
                return
            except Exception as e:
                pass

        # Server still isn't started, something's wrong
        sys.exit("Server failed to start")

    @staticmethod
    def serve(arglist):
        parser = argparse.ArgumentParser(**Commands._desc)
        parser.add_argument("port", type=int)
        args = parser.parse_args(arglist)

        basepath = os.path.dirname(os.path.abspath(__file__))
        logpath = os.path.join(basepath, "logs")
        if not os.path.isdir(logpath):
            os.mkdir(logpath)
        logpath = os.path.join(logpath, "server.log")

        logging.basicConfig(
            filename=logpath,
            filemode="w",
            format="%(levelname)-5s [%(asctime)s] %(message)s",
            level=logging.INFO)

        os.chdir(os.path.join(basepath, "..", "www"))

        class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
            def __init__(self, *args, **kwargs):
                http.server.HTTPServer.__init__(self, *args, **kwargs)

        # with http.server.HTTPServer(("", args.port), LoggingCGIHandler) as httpd:
        with ThreadingHTTPServer(("", args.port), LoggingCGIHandler) as httpd:
            sa = httpd.socket.getsockname()
            serve_message = "Serving HTTP on http://{host}:{port}/) ..."
            logging.info(serve_message.format(host=sa[0], port=sa[1]))
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                logging.info("\nKeyboard interrupt received, exiting.")
                sys.exit(0)


class Delegator(argparse.ArgumentParser):
    options = [item[0] for item in inspect.getmembers(Commands, inspect.isfunction)]
    def exit(self, status=0, message=None):
        commands = "\n  ".join(Delegator.options)
        print("{0}\nCommand options are:\n  {1}".format(message, commands))
        sys.exit(status)

def main():
    parser = Delegator()
    parser.add_argument("command", help="The command to execute.")
    parser.add_argument("args",
        nargs=argparse.REMAINDER,
        help="Arguments and options to send to the sub-command")
    args = parser.parse_args()

    if args.command in Delegator.options:
        Commands._desc = dict(
            prog="%s %s" % (os.path.basename(sys.argv[0]), sys.argv[1]),
            description=getattr(Commands, sys.argv[1]).__doc__)
        getattr(Commands, args.command)(args.args)
    else:
        parser.exit(1, "Invalid command: '{}'".format(args.command))

if __name__ == '__main__':
    main()
