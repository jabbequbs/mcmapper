#!/usr/bin/env python3

import collections
import json
import os

from PIL import Image


def get_texture(jar, blockstate):
    filename = os.path.join(jar, "blockstates", blockstate)
    if not os.path.isfile(filename):
        raise Exception("file missing (expected at %s)" % filename)

    with open(filename) as f:
        data = json.load(f)

    model = None
    if "variants" in data:
        key = sorted(data["variants"])[-1]
        model = data["variants"][key]
    elif "multipart" in data:
        applier = data["multipart"][0]["apply"]
        if type(applier) is dict:
            model = applier["model"]
        elif type(applier) is list:
            model = applier[0]["model"]

    if type(model) is list:
        model = model[0]["model"]
    elif type(model) is dict:
        model = model["model"]

    with open(os.path.join(jar, "models", *model.split("/"))+".json") as f:
        data = json.load(f)

    key = "top"
    if key not in data["textures"]:
        key = sorted(data["textures"])[-1]
    texture = data["textures"][key]

    filename = os.path.join(jar, "textures", *texture.split("/"))+".png"
    if not os.path.isfile(filename):
        raise Exception("texture file does not exist: %s" % texture)

    texture = Image.open(filename)
    if texture.mode == "P":
        texture = texture.convert("RGBA")
    result = collections.Counter(pixel for pixel in texture.getdata()
        if not (len(pixel) == 4 and pixel[-1] == 0))

    return result.most_common(1)[0][0][:3]


def main():
    version_dir = os.path.join(os.environ["APPDATA"], ".minecraft", "versions")
    versions = [(tuple(map(int, name.split("."))), name) for name in os.listdir(version_dir)]
    latest = sorted(versions)[-1][-1]
    print(latest)
    jar = os.path.join(version_dir, latest, latest, "assets", "minecraft")

    errors = {}
    # blockstates = [line.split()[0] for line in asdf.strip().splitlines()]
    blockstates = os.listdir(os.path.join(jar, "blockstates"))
    for blockstate in blockstates:
        try:
            print('"%s": bytes(%s),' % (blockstate.split(".")[0], get_texture(jar, blockstate)))
        except Exception as e:
            errors[blockstate] = str(e)

    if len(errors):
        for blockstate, error in errors.items():
            print(blockstate, ":", error)


if __name__ == '__main__':
    main()
