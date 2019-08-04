#!/usr/bin/env python3

import nbt
import os
import pyglet
import subprocess
import sys

from datetime import datetime
from pyglet.gl import *


class MainWindow(pyglet.window.Window):
    def __init__(self, rows, *args, **kwargs):
        pyglet.window.Window.__init__(self, *args, **kwargs)
        self.rows = rows
        self.labels = []
        for row in self.rows:
            self.labels.append(pyglet.text.Label("%s (%s) - %s" % (
                row["Name"], row["Folder Name"], row["Last Played"]),
                font_name="Verdana", font_size=24, x=0, y=0))
        attrs = sorted(dir(self.labels[0]))
        maxlen = max(len(attr) for attr in attrs)
        for attr in attrs:
            print("%*s\t%s" % (maxlen, attr, type(getattr(self.labels[0], attr))))

    def on_draw(self):
        self.clear()
        glLoadIdentity()
        padding = 10
        glTranslatef(padding, self.height-self.labels[0].font_size-padding, 0)
        for label in self.labels:
            label.draw()
            # print(label.content_width)
            glTranslatef(0, -48, 0)

    def on_mouse_release(self, x, y, buttons, modifiers):
        viewer = os.path.join(os.path.dirname(__file__), "viewer.py")
        subprocess.Popen([sys.executable, viewer, "world24.png"])


def main():
    minecraft_dir = os.path.join(os.environ["APPDATA"], ".minecraft", "saves")
    levels = (os.path.join(minecraft_dir, f, "level.dat") for f in os.listdir(minecraft_dir))
    columns = ["Name", "Folder Name", "Mode", "Last Played"]
    gameTypes = ["Survival", "Creative", "Adventure", "Spectator"]
    rows = []
    for level in levels:
        if not os.path.isfile(level):
            continue
        data = nbt.nbt.NBTFile(level)
        rows.append(dict(zip(columns, (
            data["Data"]["LevelName"].value,
            os.path.basename(os.path.dirname(level)),
            gameTypes[data["Data"]["Player"]["playerGameType"].value],
            datetime.fromtimestamp(data["Data"]["LastPlayed"].value/1000).strftime("%Y-%m-%d %H:%M:%S"),
            ))))
    rows.sort(key=lambda row: row["Last Played"], reverse=True)

    window = MainWindow(rows, resizable=True, width=1024, height=768, caption="Map Viewer")
    pyglet.app.run()

if __name__ == '__main__':
    main()
