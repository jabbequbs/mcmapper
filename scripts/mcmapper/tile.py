#!/usr/bin/env python3

import json
import logging
import nbt
import os

from io import BytesIO
from PIL import Image
from mapper import render_chunk
from wsgibase import Request


def app(environ, start_response):
    request = Request(environ)
    logging.info("%s %s", environ["SCRIPT_NAME"]+request.path, request.params)

    folder = os.path.join(os.environ["APPDATA"], ".minecraft", "saves", request.params["world"])
    world = nbt.world.WorldFolder(folder)

    tile_dir = os.path.join(os.path.dirname(__file__), "tiles", request.params["world"])
    if not os.path.isdir(tile_dir):
        os.makedirs(tile_dir)

    x, z = int(request.params["x"]), int(request.params["z"])
    # determine which region this tile is in
    region_x, region_z = x//4, z//4

    tile = Image.new("RGB", (128, 128), (128, 128, 128))
    if (region_x, region_z) in world.regionfiles:
        region = world.get_region(region_x, region_z)
        # determine where in the region the tile is
        minx, minz = x % 4, z % 4
        tile_filename = os.path.join(tile_dir, "tile.%s.%s.png" % (x, z))
        if os.path.isfile(tile_filename) and os.path.getmtime(tile_filename) < os.path.getmtime(region.filename):
            with open(tile_filename, "rb") as f:
                data = f.read()
            start_response("200 OK", [("Content-type", "image/png")])
            return [data]

        if x < 0:
            region_x = 3 - region_x
        if z < 0:
            region_z = 3 - region_z
        minx *= 8
        minz *= 8

        for z in range(minz, minz+8):
            for x in range(minx, minx+8):
                try:
                    chunk = region.get_chunk(x, z)
                except nbt.region.InconceivedChunk as e:
                    tile.paste(Image.new("RGB", (16, 16)), ((16*x)%128, (16*z)%128))
                else:
                    tile.paste(render_chunk(chunk, "WORLD_SURFACE"), ((16*x)%128, (16*z)%128))

        logging.info("Saving %s", tile_filename)
        tile.save(tile_filename)

    result = BytesIO()
    tile.save(result, format="PNG")

    start_response("200 OK", [("Content-type", "image/png")])
    return [result.getvalue()]
