#!/usr/bin/env python3

import os


def get_data_dir(world):
    if type(world) is not str:
        world = world.worldfolder
    return os.path.abspath(os.path.join(os.path.dirname(__file__),
        "..", "..", "data", os.path.basename(world)))

def get_asset_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__),
        "..", "..", "assets"))

def get_minecraft_basedir():
    return os.path.join(os.environ["APPDATA"], ".minecraft", "saves")

def get_minecraft_savedirs():
    """Return the absolute paths to the various minecraft save folders"""
    base_dir = get_minecraft_basedir()
    result = []
    for f in os.listdir(base_dir):
        folder = os.path.join(base_dir, f)
        if os.path.isfile(os.path.join(folder, "level.dat")):
            result.append(folder)
    return result

def get_minecraft_savedir(foldername):
    result = os.path.join(get_minecraft_basedir(), foldername)
    if not os.path.isfile(os.path.join(result, "level.dat")):
        raise FileNotFoundError(result)
    return result
