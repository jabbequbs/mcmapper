#!/usr/bin/env python3

import argparse
import os
import pyglet
import sys
import threading
import cProfile
import subprocess

import mcmapper.filesystem as fs

from glob import glob
from mcmapper.level import LevelInfo
from mcmapper.mapper import render_world, missing_blocks
from pyglet.gl import *
from pyglet.window import key as KEY


class SpriteManager(object):
    def __init__(self, folder, dimension):
        asset_dir = fs.get_asset_dir()
        self.folder = folder
        self.sprites = {}
        for sprite_file in glob(os.path.join(folder, "%s.*.png" % dimension)):
            key = tuple(map(int, os.path.basename(sprite_file).split(".")[1:3]))
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
    def __init__(self, world, *args, **kwargs):
        pyglet.window.Window.__init__(self, *args, **kwargs)
        self.level = world
        player = self.level.get_players()[0]
        self.sprites = SpriteManager(fs.get_data_dir(self.level.folder), player.dimension)
        threading.Thread(target=self.render_world).start()
        self.player_location = (player.x, player.z)
        self.indicator = pyglet.sprite.Sprite(img=pyglet.image.load(
            os.path.join(os.path.dirname(__file__), "mcmapper", "indicator.png")))
        self.indicator.x = self.player_location[0]
        self.indicator.y = -self.player_location[1]

        self.scale = 1.0
        # Center the window on the player location
        self.x = player.x-self.width/2
        self.y = -player.z-self.height/2

    def render_world(self):
        if getattr(self, "worker", None) is not None:
            return
        self.set_caption(self.caption + " - Rendering...")
        # Rendering in a subprocess keeps the main map window more responsive
        self.worker = subprocess.Popen([sys.executable, __file__, "--render", self.level.folder])
        self.worker.wait()
        player = self.level.get_players()[0]
        self.sprites = SpriteManager(fs.get_data_dir(self.level.folder), player.dimension)
        self.set_caption(self.caption.replace(" - Rendering...", ""))
        self.render_thread = None
        # TODO: trigger self.on_draw

    def on_key_release(self, key, modifiers):
        if key == KEY.R:
            self.render_thread = threading.Thread(target=self.render_world)
            self.render_thread.start()
        elif key == KEY.P:
            # Center the window on the player location
            player = self.level.get_players()[0]
            self.player_location = (player.x, player.z)
            self.x = player.x-self.width/self.scale/2
            self.y = -player.z-self.height/self.scale/2
            self.indicator.x = self.player_location[0]
            self.indicator.x = -self.player_location[1]
        elif key == KEY.I:
            print("window top left:", (self.x, self.y))
            print("player location:", self.player_location)
        elif key == KEY.PAGEUP or key == KEY.PAGEDOWN: # page up or page down
            scroll_y = -1 if key == KEY.PAGEDOWN else 1
            mouse_x = self.x + self.width/2/self.scale
            mouse_y = self.y + self.height/2/self.scale
            self.scale *= pow(1.1, scroll_y)
            self.x = mouse_x - self.width/2/self.scale
            self.y = mouse_y - self.height/2/self.scale
        elif key == KEY.LEFT or key == KEY.RIGHT:
            dx = self.width/self.scale/4
            dx = -dx if key == KEY.LEFT else dx
            self.x += dx
            if modifiers & KEY.MOD_CTRL:
                self.x += dx
        elif key == KEY.UP or key == KEY.DOWN:
            dy = self.height/self.scale/4
            dy = -dy if key == KEY.UP else dy
            self.y -= dy
            if modifiers & KEY.MOD_CTRL:
                self.y -= dy
        else:
            print("Unhandled key: %s,%s" % (key, modifiers))

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
                    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
                    sprite.draw()
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        self.indicator.draw()

        # for sprite in self.test_sprites:
        #     sprite.draw()

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self.x -= dx/self.scale
        self.y -= dy/self.scale

    def on_mouse_release(self, x, y, button, modifiers):
        """Select a chunk for debugging"""
        print("mouse click:", (x, y))
        if modifiers & 2: # CTRL is pressed
            world_x = self.x + (self.width*(x/self.width)/self.scale)
            world_z = -(self.y + (self.height*(y/self.height)/self.scale))
            region_x = int(world_x // 512)
            region_z = int(world_z // 512)
            region_origin_x = region_x * 512
            region_origin_z = region_z * 512
            chunk_x = (world_x - region_origin_x) // 16
            chunk_z = (world_z - region_origin_z) // 16
            chunk = self.level.get_region("overworld", region_x, region_z).get_chunk(chunk_x, chunk_z)
            print((world_x, world_z), (region_x, region_z))
            binn = lambda i: ("%64s" % bin(i).replace("-", "")[2:]).replace(" ", "0")
            print("Heightmap:")
            print("\n".join(binn(e) for e in chunk["Level"]["Heightmaps"]["WORLD_SURFACE"]))
            # sea level section
            section = next(section for section in chunk["Level"]["Sections"] if section["Y"].value == 3)
            print("Palette:")
            print("\n".join(str(e) for e in section["Palette"]))
            print("Blocks:")
            print("\n".join(binn(e) for e in section["BlockStates"]))
            print("Palette length:", len(bin(len(section["Palette"])-1))-2)
            # import pdb; pdb.set_trace()

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        mouse_x = self.x + x/self.scale
        mouse_y = self.y + y/self.scale
        self.scale *= pow(1.1, scroll_y)
        self.x = mouse_x - x/self.scale
        self.y = mouse_y - y/self.scale

    def get_tile_bounds(self):
        """Return the tile indexes for the current viewport"""
        minX = int(self.x // 512)
        maxX = int(minX + ((self.width/self.scale)//512))+1
        maxY = -int(self.y // 512)
        minY = int(maxY - ((self.height/self.scale)//512))-2
        return minX, maxX, minY, maxY


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("world", nargs="?")
    parser.add_argument("--render", action="store_true",
        help="Regenerate the tiles and world map for the specified world")
    args = parser.parse_args()

    if args.world:
        args.world = LevelInfo(args.world)
    else:
        folders = [LevelInfo(f) for f in fs.get_minecraft_savedirs()]
        folders.sort(key=lambda f: f.last_played)
        args.world = folders[-1]
    if args.render:
        # cProfile.runctx("render_world(args.world.folder)", globals(), locals())
        render_world(args.world.folder)
        if len(missing_blocks):
            print("Missing blocks:")
            print("  " + "\n  ".join(sorted(missing_blocks.keys())))
        return

    window = MapViewerWindow(args.world,
        resizable=True, width=1024, height=768, caption="Map Viewer - %s" % args.world.name)
    pyglet.app.run()


if __name__ == '__main__':
    main()
