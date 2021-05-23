#!/usr/bin/env python3

import nbt
import os

from datetime import datetime
from glob import glob
from mcmapper.filesystem import get_minecraft_basedir


game_types = ["Survival", "Creative", "Adventure", "Spectator"]
dimensions = {"minecraft:the_nether": "nether", "minecraft:overworld": "overworld", "minecraft:the_end": "end"}
dimension_folders = {
    "nether": os.path.join("DIM-1", "region"),
    "overworld": "region",
    "end": os.path.join("DIM1", "region"),
    }


class PlayerInfo(object):
    def __init__(self, filename):
        playerInfo = nbt.nbt.NBTFile(filename)
        self.dimension = dimensions[playerInfo["Dimension"].value]
        self.x, self.y, self.z = (t.value for t in playerInfo["Pos"])
        self.yaw, self.pitch = (t.value for t in playerInfo["Rotation"])


class LevelInfo(object):
    def __init__(self, folder):
        if not os.path.isdir(os.path.join(folder, "level.dat")):
            folder = os.path.join(get_minecraft_basedir(), folder)
        self.folder = folder
        base = nbt.nbt.NBTFile(os.path.join(folder, "level.dat"))["Data"]
        self.spawnX = base["SpawnX"].value
        self.spawnZ = base["SpawnZ"].value
        self.name = base["LevelName"]
        self.game_type = game_types[base["Player"]["playerGameType"].value]
        self.last_played = datetime.fromtimestamp(
            base["LastPlayed"].value/1000).strftime("%Y-%m-%d %H:%M:%S")

    def get_players(self):
        filenames = glob(os.path.join(self.folder, "playerdata", "*.dat"))
        return [PlayerInfo(f) for f in filenames]

    def get_regions(self, dimension):
        return glob(os.path.join(self.folder, dimension_folders[dimension], "*.mca"))

    def get_region(self, dimension, x, z):
        filename = os.path.join(self.folder, dimension_folders[dimension], "r.%s.%s.mca" % (x, z))
        if not os.path.isfile(filename):
            raise Exception("No such region: %s(%s, %s)" % (dimension, x, z))
        return nbt.region.RegionFile(filename)
