#!/usr/bin/env python3

import collections
import json
import os
import zipfile

from PIL import Image


def get_texture(jar, data):
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

    model = model.replace("minecraft:", "")
    model = f"assets/minecraft/models/{model}.json"
    data = json.loads(jar.read(model).decode("utf-8"))

    key = "top"
    if key not in data["textures"]:
        key = sorted(data["textures"])[-1]
    texture_file = data["textures"][key].replace("minecraft:", "")
    texture_file = f"assets/minecraft/textures/{texture_file}.png"

    with jar.open(texture_file) as image_data:
        texture = Image.open(image_data)
        texture.load()

    if texture.mode == "P":
        texture = texture.convert("RGBA")
    result = collections.Counter(pixel for pixel in texture.getdata()
        if not (len(pixel) == 4 and pixel[-1] == 0))

    return ", ".join(map(str, result.most_common(1)[0][0][:3]))


def main():
    version_dir = os.path.join(os.environ["APPDATA"], ".minecraft", "versions")
    versions = []
    for dirname in os.listdir(version_dir):
        try:
            versions.append((tuple(map(int, dirname.split("."))), dirname))
        except ValueError:
            pass
    latest = sorted(versions)[-1][-1]
    print(latest)

    with zipfile.ZipFile(os.path.join(version_dir, latest, f"{latest}.jar")) as jar:
        errors = {}
        filenames = jar.namelist()
        blockstates = [f for f in filenames if f.startswith("assets/minecraft/blockstates/")]
        for blockstate in blockstates:
            basename = blockstate.split("/")[-1].split(".")[0]
            try:
                info = json.loads(jar.read(blockstate).decode("utf-8"))
                print(f'"{basename}": bytes(({get_texture(jar, info)})),')
            except Exception as e:
                errors[basename] = f"{type(e)}: {e}"

    if len(errors):
        for blockstate, error in errors.items():
            print(blockstate, ":", error)


if __name__ == '__main__':
    main()
