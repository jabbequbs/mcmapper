#!/usr/bin/env python3

import json
import logging
import os
import sqlite3

class config(object):
    db = None
    pks = {}

def getPk(tblname):
    tblname = tblname.upper()
    if tblname not in config.pks:
        # cursor = config.db.cursor()
        # cursor.execute("pragma table_info(%s)" % tblname)
        # config.pks[tblname] = next(row[1] for row in cursor if row[-1]).upper()
        config.pks[tblname] = "ROWID"
    return config.pks[tblname]

class Commands(object):
    def load(request):
        result = {}
        cursor = config.db.cursor()
        cursor.execute("select name from sqlite_master where type = 'table'")
        for table, in cursor.fetchall():
            cursor.execute("select rowid rowid, * from %s" % table)
            columns = [d[0].upper() for d in cursor.description]
            result[table] = {
                "columns": columns, "data": cursor.fetchall(), "pk": getPk(table)}
        return result

    def save(request):
        """
        request.json will be an object with possible keys deletes/updates/inserts

        If "inserts" exists, there will also be a key "columns"

        The value of "deletes" is an object whose keys are table names and values
         are lists of primary key values to be deleted.

        The value of "updates" is an object whose keys are table names and values
         are objects whose keys are primary key values and values are objects
         whose keys are column names and values are new column values.

        The value of "inserts" is an object whose keys are table names and values
         are lists of tuples representing rows in that table.

        The value of "columns" is an object whose keys are table names and values
         are tuples of column names corresponding to the values for that table
         in "inserts".
        """
        assert request.method == "POST"
        cursor = config.db.cursor()
        for tblname, keys in request.json.get("deletes", {}).items():
            pkCol = getPk(tblname)
            for pk in keys:
                logging.info("deleting %s[%s=%s]", tblname, pkCol, pk)
                try:
                    cursor.execute("delete from %s where %s = ?" % (tblname, pkCol), (pk,))
                except Exception as exc:
                    logging.error(repr(exc))
                    return "Error encountered deleting %s[%s=%s]:\n%s" % (
                        tblname, pkCol, pk, exc)

        for tblname, updates in request.json.get("updates", {}).items():
            pkCol = getPk(tblname)
            for pk, columns in updates.items():
                columnNames = sorted(columns)
                stmt = "update %s set %s where %s = ?" % (
                    tblname, ", ".join("%s = ?" % col for col in columnNames), pkCol)
                logging.info(stmt)
                params = tuple(columns[col] for col in columnNames) + (pk,)
                logging.info(str(params))
                try:
                    cursor.execute(stmt, params)
                except Exception as exc:
                    logging.error(repr(exc))
                    return "Error encountered updating %s[%s=%s]:\n%s" % (
                        tblname, pkCol, pk, exc)

        for tblname, inserts in request.json.get("inserts", {}).items():
            pkCol = getPk(tblname)
            pkIndex = None
            columns = request.json["columns"][tblname]
            logging.info("%s (%s): %s", tblname, pkCol, columns)
            if pkCol in columns:
                pkIndex = columns.index(pkCol)
                del columns[pkIndex]
            stmt = "insert into %s (%s) values (%s)" % (
                tblname, ", ".join(columns), ", ".join("?" for _ in columns))
            logging.info(stmt)
            for row in inserts:
                params = list(row)
                if pkIndex is not None:
                    del params[pkIndex]
                logging.info(params)
                params = tuple(params)
                try:
                    cursor.execute(stmt, params)
                except Exception as exc:
                    logging.error(repr(exc))
                    return "Error inserting row into %s\n%s\n\n%s" % (
                        tblname, row, exc)

        return "Success"

def app(environ, start_response):
    from wsgibase import Request
    request = Request(environ)

    logging.info("%s %s", environ["SCRIPT_NAME"]+request.path, request.params)
    with sqlite3.connect(request.params["db"]) as connection:
        cursor = connection.cursor()
        result, = cursor.execute("select count(*) from sqlite_master").fetchone()
        if result == 0:
            with open("schema.sql") as f:
                connection.executescript(f.read())
        cursor.execute("pragma foreign_keys = ON")
        config.db = connection
        result = getattr(Commands, request.params["action"])(request)

    if type(result) is str:
        content_type = "text/plain; charset=utf-8"
        result = result.encode("utf-8")
    else:
        content_type = "application/json; charset=utf-8"
        result = json.dumps(result).encode("utf-8")

    start_response("200 OK", [("Content-type", content_type)])
    return [result]
