#!/usr/bin/env python3

import json
import logging
import nbt
import os

from datetime import datetime
from wsgibase import Request


def app(environ, start_response):
    request = Request(environ)
    logging.info("%s %s", environ["SCRIPT_NAME"]+request.path, request.params)

    minecraft_dir = os.path.join(os.environ["APPDATA"], ".minecraft", "saves")
    levels = (os.path.join(minecraft_dir, f, "level.dat") for f in os.listdir(minecraft_dir))

    columns = ["Name", "Folder Name", "Mode", "Last Played"]
    gameTypes = ["Survival", "Creative", "Adventure", "Spectator"]
    result = {"levelInfoCols": columns, "levelInfoData": []}
    for level in levels:
        if not os.path.isfile(level):
            continue
        data = nbt.nbt.NBTFile(level)
        result["levelInfoData"].append([
            data["Data"]["LevelName"].value,
            os.path.basename(os.path.dirname(level)),
            gameTypes[data["Data"]["Player"]["playerGameType"].value],
            datetime.fromtimestamp(data["Data"]["LastPlayed"].value/1000).strftime("%Y-%m-%d %H:%M:%S"),
            ])
    result["levelInfoData"].sort(key=lambda l: l[-1], reverse=True)

    if type(result) is str:
        content_type = "text/plain; charset=utf-8"
        result = result.encode("utf-8")
    else:
        content_type = "application/json; charset=utf-8"
        result = json.dumps(result).encode("utf-8")

    start_response("200 OK", [("Content-type", content_type)])
    return [result]
