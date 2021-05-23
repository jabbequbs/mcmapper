#!/usr/bin/env python3

import argparse
import os
import pyglet
import sys
import threading
import cProfile
import subprocess
import concurrent.futures

import mcmapper.filesystem as fs

from glob import glob
from mcmapper.level import LevelInfo
from mcmapper.mapper import render_world, missing_blocks, render_region
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
        self.dimension = player.dimension
        self.sprites = SpriteManager(fs.get_data_dir(self.level.folder), player.dimension)
        self.player_location = (player.x, player.z)
        self.indicator = pyglet.sprite.Sprite(img=pyglet.image.load(
            os.path.join(os.path.dirname(__file__), "mcmapper", "indicator.png")))
        self.indicator.x = self.player_location[0]
        self.indicator.y = -self.player_location[1]
        self.sprite_lock = threading.Lock()
        self.scale = 2.0
        # Center the window on the player location
        self.x = player.x-self.width/(2*self.scale)
        self.y = -player.z-self.height/(2*self.scale)
        self.gui = self.setup_gui()
        self.progress = None
        self.cancel_render = False
        pyglet.clock.schedule_interval(self.on_draw, 0.5)
        self.render_thread = threading.Thread(target=self.render_world)
        self.render_thread.start()
        self.workers = []

    def setup_gui(self):
        self.font_spacing = None
        btn_height = None
        # TODO: this should be a pyglet.graphics.Batch, but then the borders dont render
        self.gui = []
        self.button_regions = {}
        self.rectangles = {}
        self.pressed_button = None
        y = self.height
        for text in ("REFRESH MAP", "LOCATE PLAYER", "CHANGE WORLD", "CHANGE DIMENSION"):
            label = pyglet.text.Label(text, bold=True, color=(0,0,0, 255), anchor_y="center")
            if self.font_spacing is None:
                self.font_height = label.content_height
                self.font_spacing = label.content_height/2
                btn_height = label.content_height*2
            y -= self.font_spacing+btn_height
            label.x = self.font_spacing*2
            label.y = y + btn_height/2
            xMin, yMin, xMax, yMax = (self.font_spacing, y, label.content_width+self.font_spacing*3, y+btn_height)
            self.button_regions[(xMin, yMin, xMax, yMax)] = text
            self.gui.append(pyglet.shapes.Rectangle(xMin, yMin, xMax-xMin, yMax-yMin, color=(192,192,192)))
            self.rectangles[text] = self.gui[-1]
            self.gui.append(pyglet.shapes.Line(xMin, yMin, xMax, yMin, 5, color=(0,0,0)))
            self.gui.append(pyglet.shapes.Line(xMin, yMin, xMin, yMax, 5, color=(0,0,0)))
            self.gui.append(pyglet.shapes.Line(xMin, yMax, xMax, yMax, 5, color=(0,0,0)))
            self.gui.append(pyglet.shapes.Line(xMax, yMin, xMax, yMax, 5, color=(0,0,0)))
            self.gui.append(label)
        return self.gui

    def render_world(self):
        if self.render_thread is not None:
            return
        self.progress = ("Checking regions...", (0, 100))
        dimension = self.dimension
        region_files = self.level.get_regions(dimension)
        regions = []
        for filename in region_files:
            parts = os.path.basename(filename).split(".")
            regions.append((int(parts[1]), int(parts[2])))
        data_dir = fs.get_data_dir(self.level.folder)
        renderable_regions = []
        for idx, region in enumerate(regions):
            self.progress = ("Checking regions...", (idx, len(regions)))
            x, z = region
            try:
                region = self.level.get_region(dimension, x, z)
            except Exception as e:
                print("\n%s" % e)
                continue
            tile_file = os.path.join(data_dir, "%s.%s.%s.png" % (dimension, x, z))
            if not os.path.isfile(tile_file) or os.path.getmtime(tile_file) < os.path.getmtime(region.filename):
                renderable_regions.append((tile_file, x, z))

        def _render_region(filename, region_x, region_z):
            if self.cancel_render:
                return
            worker = subprocess.Popen([sys.executable, __file__, self.level.folder,
                "--region", f"{dimension},{region_x},{region_z}"])
            self.workers.append(worker)
            if worker.wait() == 0:
                with self.sprite_lock:
                    self.sprites.sprites[region_info] = filename

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(_render_region, *info) for info in renderable_regions]
            for future in enumerate(concurrent.futures.as_completed(futures)):
                self.progress = (f"Rendering {len(renderable_regions)} regions...", (idx, len(renderable_regions)))

        self.workers = []
        self.render_thread = None
        self.progress = None

    def on_key_release(self, key, modifiers):
        if key == KEY.I:
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

    def on_draw(self, dt=None):
        self.clear()
        glLoadIdentity()
        glScalef(self.scale, self.scale, 1)
        glTranslatef(-self.x, -self.y, 0)

        minX, maxX, minY, maxY = self.get_tile_bounds()
        with self.sprite_lock:
            for x in range(minX, maxX+1):
                for y in range(minY, maxY+1):
                    sprite = self.sprites[(x, y)]
                    if sprite:
                        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
                        sprite.draw()
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        self.indicator.draw()

        glLoadIdentity()
        for item in self.gui:
            item.draw()

        if self.progress:
            pyglet.shapes.Rectangle(0, 0, self.width, 3*self.font_height+self.font_spacing, color=(192,192,192)).draw()
            pyglet.shapes.Line(0, 3*self.font_height+self.font_spacing, self.width, 3*self.font_height+self.font_spacing, 5, color=(0,0,0)).draw()
            pyglet.shapes.Rectangle(self.font_spacing, self.font_spacing,
                self.width-2*self.font_spacing, self.font_height, color=(255,255,255)).draw()
            progress_width = self.progress[1][0] / self.progress[1][1] * (self.width-3*self.font_spacing)
            pyglet.shapes.Rectangle(self.font_spacing, self.font_spacing,
                progress_width, self.font_height, color=(64, 255, 64)).draw()
            pyglet.text.Label(self.progress[0].upper(), bold=True, x=self.font_spacing, y=self.font_height*2+self.font_spacing,
                anchor_y="center", color=(0,0,0,255)).draw()

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self.pressed_button:
            return
        self.x -= dx/self.scale
        self.y -= dy/self.scale

    def on_mouse_press(self, x, y, button, modifiers):
        for region, command in self.button_regions.items():
            xMin, yMin, xMax, yMax = region
            if xMin < x < xMax and yMin < y < yMax:
                self.pressed_button = command
                self.rectangles[command].color = (255,255,255)

    def on_mouse_release(self, x, y, button, modifiers):
        for region, command in self.button_regions.items():
            xMin, yMin, xMax, yMax = region
            if command == self.pressed_button and xMin < x < xMax and yMin < y < yMax:
                if command == "REFRESH MAP":
                    if not self.render_thread:
                        self.render_thread = threading.Thread(target=self.render_world)
                        self.render_thread.start()
                elif command == "LOCATE PLAYER":
                    player = self.level.get_players()[0]
                    self.player_location = (player.x, player.z)
                    self.x = player.x-self.width/self.scale/2
                    self.y = -player.z-self.height/self.scale/2
                    self.indicator.x = self.player_location[0]
                    self.indicator.z = -self.player_location[1]

        if self.pressed_button:
            self.rectangles[self.pressed_button].color = (192, 192, 192)
            self.pressed_button = None

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
    parser.add_argument("--region",
        help="Render a certain region for the specified world")
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
    elif args.region:
        dimension, x, z = args.region.split(",")
        x, z = int(x), int(z)
        data_dir = fs.get_data_dir(args.world.folder)
        filename = os.path.join(data_dir, f"{dimension}.{x}.{z}.png")
        render_region(args.world.get_region(dimension, x, z)).save(filename)
    else:
        window = MapViewerWindow(args.world,
            resizable=True, width=1024, height=768, caption="Map Viewer - %s" % args.world.name)
        pyglet.app.run()
        print("Cancelling pending renders...")
        window.cancel_render = True
        print("Terminating render processes...")
        for worker in window.workers:
            worker.terminate()
        print("Waiting for render thread...")
        if window.render_thread:
            window.render_thread.join()


if __name__ == '__main__':
    main()
