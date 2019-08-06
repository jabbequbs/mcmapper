#!/usr/bin/env python3

import argparse
import os
import pyglet

import mcmapper.filesystem as fs

from glob import glob
from mcmapper.level import LevelInfo
from pyglet.gl import *


class SpriteManager(object):
    def __init__(self, folder):
        asset_dir = fs.get_asset_dir()
        self.folder = folder
        self.sprites = {}
        for sprite_file in glob(os.path.join(folder, "*.png")):
            key = tuple(map(int, os.path.basename(sprite_file).split(".")[:2]))
            self.sprites[key] = sprite_file

    def __getitem__(self, key):
        if key not in self.sprites:
            return None
        result = self.sprites[key]
        if type(result) is str:
            result = pyglet.sprite.Sprite(img=pyglet.image.load(result))
            result.x = result.width*key[0]
            result.y = -result.height*(key[1]+1)
            self.sprites[key] = result
        return result


class MapViewerWindow(pyglet.window.Window):
    def __init__(self, world_folder, *args, **kwargs):
        pyglet.window.Window.__init__(self, *args, **kwargs)
        self.sprites = SpriteManager(fs.get_data_dir(world_folder))
        self.level = LevelInfo(world_folder)
        # self.test_sprites = [
        #     self.sprites[(0, 0)],
        #     self.sprites[(0, -1)],
        #     self.sprites[(0, 1)],
        # ]

        # thing = self.sprite
        # attrs = sorted(dir(thing))
        # maxlen = max(len(attr) for attr in attrs)
        # for attr in attrs:
        #     print("%*s\t%s" % (maxlen, attr, type(getattr(thing, attr))))

        self.scale = 1.0
        player = self.level.get_players()[0] # (x, y ,z)
        self.x = player[0]-self.width/2
        self.y = -player[2]-self.height/2
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

    def on_activate(self):
        player = self.level.get_players()[0] # (x, y ,z)
        self.x = player[0]-self.width/self.scale/2
        self.y = -player[2]-self.height/self.scale/2

    def on_draw(self):
        self.clear()
        glLoadIdentity()
        glScalef(self.scale, self.scale, 1)
        glTranslatef(-self.x, -self.y, 0)

        minX, maxX, minY, maxY = self.get_tile_bounds()
        for x in range(minX, maxX+1):
            for y in range(minY, maxY+1):
                sprite = self.sprites[(x, y)]
                if sprite:
                    sprite.draw()

        # for sprite in self.test_sprites:
        #     sprite.draw()

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self.x -= dx/self.scale
        self.y -= dy/self.scale

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        mouse_x = self.x + x/self.scale
        mouse_y = self.y + y/self.scale
        self.scale *= pow(1.1, scroll_y)
        self.x = mouse_x - x/self.scale
        self.y = mouse_y - y/self.scale

    # def on_mouse_release(self, x, y, buttons, modifiers):
    #     minX, maxX, minY, maxY = self.get_tile_bounds()
    #     print("X:", (minX, maxX), maxX-minX)
    #     print("Y:", (minY, maxY), maxY-minY)

    def get_tile_bounds(self):
        """Return the tile indexes for the current viewport"""
        minX = int(self.x // 512)
        maxX = int(minX + ((self.width/self.scale)//512))+1
        maxY = -int(self.y // 512)
        minY = int(maxY - ((self.height/self.scale)//512))-2
        return minX, maxX, minY, maxY


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("world")
    args = parser.parse_args()

    window = MapViewerWindow(args.world,
        resizable=True, width=1024, height=768, caption="Map Viewer")
    pyglet.app.run()


if __name__ == '__main__':
    main()
