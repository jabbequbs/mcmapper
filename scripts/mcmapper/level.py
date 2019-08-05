#!/usr/bin/env python3

import nbt
import os

from datetime import datetime
from glob import glob


game_types = ["Survival", "Creative", "Adventure", "Spectator"]

class LevelInfo(object):
    def __init__(self, folder):
        self.folder = folder
        base = nbt.nbt.NBTFile(os.path.join(folder, "level.dat"))["Data"]
        self.spawnX = base["SpawnX"].value
        self.spawnZ = base["SpawnZ"].value
        self.players = []
        for player_file in glob(os.path.join(folder, "playerdata", "*.dat")):
            playerInfo = nbt.nbt.NBTFile(player_file)
            self.players.append(tuple(i.value for i in playerInfo["Pos"]))
        self.name = base["LevelName"]
        self.game_type = game_types[base["Player"]["playerGameType"].value]
        self.last_played = datetime.fromtimestamp(
            base["LastPlayed"].value/1000).strftime("%Y-%m-%d %H:%M:%S")
