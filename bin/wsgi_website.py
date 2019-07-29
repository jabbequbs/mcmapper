#!/usr/bin/env python3

import argparse
import cmd
import os
import posixpath
import socket
import subprocess
import sys
import time
import urllib.parse

from http.server import SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn
from traceback import format_exc
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server, WSGIServer, WSGIRequestHandler, ServerHandler


class MyHandler(WSGIRequestHandler, SimpleHTTPRequestHandler):
    api_url = "/cgi-bin/main.py"
    doc_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "www"))

    def handle_one_request(self):
        """Handle a single HTTP request."""
        try:
            self.raw_requestline = self.rfile.readline(65537)
            if len(self.raw_requestline) > 65536:
                self.requestline = ''
                self.request_version = ''
                self.command = ''
                self.send_error(HTTPStatus.REQUEST_URI_TOO_LONG)
                return
            if not self.raw_requestline:
                self.close_connection = True
                return
            if not self.parse_request():
                # An error code has been sent, just exit
                return

            if self.path.lower().startswith(self.api_url):
                handler = ServerHandler(
                    self.rfile, self.wfile, self.get_stderr(), self.get_environ()
                )
                handler.request_handler = self      # backpointer for logging
                handler.run(self.server.get_app())
                self.close_connection = True
            elif self.command not in ("GET", "HEAD"):
                self.send_error(
                    HTTPStatus.NOT_IMPLEMENTED,
                    "Unsupported method (%r)" % self.command)
            else:
                f = self.send_head()
                if f:
                    try:
                        if self.command == "GET":
                            self.copyfile(f, self.wfile)
                    finally:
                        f.close()
            self.wfile.flush() #actually send the response if not already done.
        except socket.timeout as e:
            #a read or a write timed out.  Discard this connection
            self.log_error("Request timed out: %r", e)
            self.close_connection = True
            return

    def translate_path(self, path):
        """Adapted from SimpleHTTPRequestHandler.translate_path"""
        # abandon query parameters
        path = path.split('?',1)[0]
        path = path.split('#',1)[0]
        # Don't forget explicit trailing slash when normalizing. Issue17324
        trailing_slash = path.rstrip().endswith('/')
        try:
            path = urllib.parse.unquote(path, errors='surrogatepass')
        except UnicodeDecodeError:
            path = urllib.parse.unquote(path)
        path = posixpath.normpath(path)
        path = os.path.join(self.doc_root, *(word for word in path.split("/")
            if word and not (os.path.dirname(word) or word in (os.curdir, os.pardir))))
        if trailing_slash:
            path += '/'
        return path

    def handle(self):
        """Handle multiple requests if necessary."""
        SimpleHTTPRequestHandler.handle(self)


class MyApplication(object):
    api_url = "/cgi-bin/main.py"

    def __call__(self, environ, start_response):
        try:
            return self._handle(environ, start_response)
        except Exception as e:
            info = format_exc().strip()
            start_response("500 Server Error", [("Content-Type", "text/plain; charset=utf-8")])
            return [info.encode("utf-8")]

    def _handle(self, environ, start_response):
        params = {k:v[0] for k,v in parse_qs(environ["QUERY_STRING"]).items()}
        if environ["PATH_INFO"].endswith("/index.html"):
            with open("index.html", "rb") as f:
                response = f.read()
            start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
            return [response]

        elif "duration" in params:
            time.sleep(int(params["duration"]))
            start_response("200 OK", [("Content-Type", "text/plain; charset=utf-8")])
            return [("Slept for %s seconds" % params["duration"]).encode("utf-8")]

        else:
            start_response("404 Not Found", [("Content-Type", "text/plain; charset=utf-8")])
            return [b"No such page"]


def server(address, port):
    # https://gist.github.com/coffeesnake/3093598
    class ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
        pass

    with make_server(address, port, MyApplication(), ThreadingWSGIServer, MyHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("Interrupt received, exiting")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", action="store_true")
    args = parser.parse_args()

    if args.server:
        os.chdir(os.path.dirname(__file__))
        server("", 9002)
        return

    worker = subprocess.Popen([sys.executable, __file__, "--server"])

    class ServerShell(cmd.Cmd):
        intro = "WSGI Server development shell.  Type help to list commands"
        prompt = ""

        def do_restart(self, arg):
            """Restart the server"""
            nonlocal worker
            print("Terminating worker...")
            worker.terminate()
            worker.wait()
            print("Restarting...")
            worker = subprocess.Popen([sys.executable, __file__, "--server"])
            print("New worker PID = %s" % worker.pid)

        def do_quit(self, arg):
            """Stop the server and quit the shell"""
            print("Terminating worker...")
            worker.terminate()
            worker.wait()
            return True

    try:
        ServerShell().cmdloop()
    except KeyboardInterrupt:
        print()
        worker.terminate()
        worker.wait()

if __name__ == '__main__':
    main()
