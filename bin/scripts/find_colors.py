#!/usr/bin/env python3

import argparse
import collections
import json
import os

from PIL import Image


def get_texture(jar, blockstate):
    filename = os.path.join(jar, "blockstates", blockstate+".json")
    if not os.path.isfile(filename):
        raise Exception("file missing (expected at %s)" % filename)

    with open(filename) as f:
        data = json.load(f)

    if "variants" not in data:
        raise Exception("no variants found")

    key = sorted(data["variants"])[-1]
    model = data["variants"][key]
    if type(model) is list:
        model = model[0]["model"]
    else:
        model = model["model"]

    with open(os.path.join(jar, "models", *model.split("/"))+".json") as f:
        data = json.load(f)

    key = sorted(data["textures"])[-1]
    texture = data["textures"][key]

    filename = os.path.join(jar, "textures", *texture.split("/"))+".png"
    if not os.path.isfile(filename):
        raise Exception("texture file does not exist: %s" % texture)

    texture = Image.open(filename)
    result = collections.Counter(pixel for pixel in texture.getdata()
        if not (len(pixel) == 4 and pixel[-1] == 0))
    return result.most_common(1)[0][0][:3]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("missing", nargs="?", default="scripts\\missing.log")
    args = parser.parse_args()

    version_dir = os.path.join(os.environ["APPDATA"], ".minecraft", "versions")
    versions = [(tuple(map(int, name.split("."))), name) for name in os.listdir(version_dir)]
    latest = sorted(versions)[-1][-1]
    jar = os.path.join(version_dir, latest, latest, "assets", "minecraft")

    with open(args.missing) as f:
        missing = f.read().splitlines()

    errors = {}
    for blockstate in missing:
        try:
            print(blockstate, get_texture(jar, blockstate))
        except Exception as e:
            errors[blockstate] = str(e)

    if len(errors):
        for blockstate, error in errors.items():
            print(blockstate, ":", error)


if __name__ == '__main__':
    main()
