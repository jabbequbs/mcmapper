#!/usr/bin/env python3

import nbt
import os

from datetime import datetime
from glob import glob
from mcmapper.filesystem import get_minecraft_basedir


game_types = ["Survival", "Creative", "Adventure", "Spectator"]

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
        result = []
        for player_file in glob(os.path.join(self.folder, "playerdata", "*.dat")):
            playerInfo = nbt.nbt.NBTFile(player_file)

            # thing = playerInfo
            # attrs = sorted(dir(thing))
            # maxlen = max(len(attr) for attr in attrs)
            # for attr in attrs:
            #     print("%*s\t%s" % (maxlen, attr, type(getattr(thing, attr))))

            result.append(tuple(i.value for i in playerInfo["Pos"]))
        return result
