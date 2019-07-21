#! /usr/bin/env python3

import json
import logging
import sys

from wsgiref.headers import Headers
from urllib.parse import parse_qs
from http.server import BaseHTTPRequestHandler
from http.cookies import SimpleCookie
from cgi import FieldStorage
from traceback import format_exc

response_codes = {k:v[0] for k,v in BaseHTTPRequestHandler.responses.items()}

class Request(object):
    def __init__(self, env):
        self.method = env["REQUEST_METHOD"]
        self.path = (env["PATH_INFO"] or "").lower()
        self.headers = Headers([(k[5:].replace("_", "-"), v)
            for k,v in env.items() if k.startswith("HTTP_")])
        params = parse_qs(env["QUERY_STRING"])
        if env["CONTENT_LENGTH"] and env["CONTENT_LENGTH"] != "0":
            content_type = env["CONTENT_TYPE"].lower()
            length = int(env["CONTENT_LENGTH"])
            body = env.get("wsgi.input", sys.stdin).read(length)
            assert content_type.startswith("application/json")
            if type(body) is bytes:
                body = body.decode("utf-8")
            self.json = json.loads(body)
            # if type(self.json) is dict:
            #     params.update(self.json)
            # elif content_type.startswith("application/x-www-form-urlencoded"):
            #     body = env["wsgi.input"].read(length)
            #     params.update(parse_qs(body.decode("utf-8")))
            # elif content_type.startswith("multipart/form-data"):
            #     form = FieldStorage(fp=env["wsgi.input"], environ=env)
            #     params.update({key:form[key] for key in form.keys()})
            # else:
            #     raise Exception("Can't handle %s" % content_type)
        self.params = {k: v[0] if type(v) is list else v for k,v in params.items()}
        self.env = env
        self.cookies = SimpleCookie(self.headers["Cookie"])

    def __getitem__(self, key):
        from_params = self.params.get(key)
        return from_params if from_params is not None else self.get_cookie(key)

    def __setitem__(self, key, value):
        self.params[key] = value

    def get_cookie(self, cookiename):
        if cookiename in self.cookies:
            return self.cookies[cookiename].value
        return None


class ErrorCatcher(object):
    def __init__(self, child):
        self.child = child

    def __call__(self, environ, start_response):
        try:
            return self.child(environ, start_response)
        except Exception as e:
            details = format_exc().strip()
            logging.error(str(e) + "\n" + details)
            start_response("500 Server Error",
                    [("Content-Type", "text/plain; charset=utf-8")])
            return [details.encode("utf-8")]
