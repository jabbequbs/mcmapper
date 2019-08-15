#!/usr/bin/env python3

import nbt
import os
import pyglet
import subprocess
import sys

import mcmapper.filesystem as fs

from datetime import datetime
from mcmapper.level import LevelInfo
from pyglet.gl import *


class MainWindow(pyglet.window.Window):
    def __init__(self, rows, *args, **kwargs):
        pyglet.window.Window.__init__(self, *args, **kwargs)
        self.rows = rows
        self.labels = []
        for row in self.rows:
            self.labels.append(pyglet.text.Label("%s (%s) - %s" % (
                row["Name"], os.path.basename(row["Folder Name"]), row["Last Played"]),
                font_name="Verdana", font_size=24, x=0, y=0))
        self.bg = pyglet.image.load(os.path.join(fs.get_asset_dir(), "bg.png"))
        sprite = pyglet.sprite.Sprite(img=self.bg)
        sprite.scale = self.width/sprite.width
        self.bgSprite = sprite
        # thing = self.labels[0]
        # attrs = sorted(dir(thing))
        # maxlen = max(len(attr) for attr in attrs)
        # for attr in attrs:
        #     print("%*s\t%s" % (maxlen, attr, type(getattr(thing, attr))))
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

    def on_draw(self):
        self.clear()
        glLoadIdentity()
        self.bgSprite.draw()
        # pyglet.graphics.draw_indexed(4, GL_TRIANGLES, [0, 1, 2, 0, 2, 3],
        #     ("v2i", (100, 100, 150, 100, 150, 150, 100, 150)),
        #     ("c3B", (255, 0, 0, 0, 255, 0, 255, 0, 0, 0, 255, 0)))
        padding = 10
        glTranslatef(padding, self.height-self.labels[0].font_size-padding, 0)
        for label in self.labels:
            label.draw()
            glTranslatef(0, -48, 0)

    def on_mouse_release(self, x, y, buttons, modifiers):
        viewer = os.path.join(os.path.dirname(__file__), "viewer.py")
        subprocess.Popen([sys.executable, viewer, self.rows[0]["Folder Name"]])


def main():
    folders = fs.get_minecraft_savedirs()
    columns = ["Name", "Folder Name", "Mode", "Last Played"]
    gameTypes = ["Survival", "Creative", "Adventure", "Spectator"]
    rows = []
    for folder in folders:
        level = LevelInfo(folder)
        rows.append(dict(zip(columns, (
            level.name, level.folder, level.game_type, level.last_played))))
    rows.sort(key=lambda row: row["Last Played"], reverse=True)

    window = MainWindow(rows, resizable=False, width=1280, height=720, caption="Map Viewer")
    pyglet.app.run()

if __name__ == '__main__':
    main()
