#!/usr/bin/env python3

import argparse
import concurrent.futures
import cProfile
import json
import nbt
import os
import pyglet
import subprocess
import sys
import threading
import time

import mcmapper.filesystem as fs

from glob import glob
from mcmapper.level import LevelInfo
from mcmapper.mapper import render_world, missing_blocks, render_region
from mcmapper.data import block_colors
from pyglet.gl import *
from pyglet.window import key as KEY


class SpriteManager(object):
    def __init__(self, folder, dimension):
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


class Indicator(object):
    def __init__(self, window):
        self.x, self.y, self.r = 0, 0, 0
        self.window = window
        center_y = -10/3
        self.parts = [
            pyglet.shapes.Triangle(0, 10-center_y, -5, -10-center_y, 5, -10-center_y, color=(255,0,0)),
            pyglet.shapes.Line(0, 10-center_y, -5, -10-center_y, 1, color=(0,0,0)),
            pyglet.shapes.Line(0, 10-center_y, 5, -10-center_y, 1, color=(0,0,0)),
            pyglet.shapes.Line(-5, -10-center_y, 5, -10-center_y, 1, color=(0,0,0)),
        ]

    def update(self, player):
        self.x = player.x
        self.y = -player.z
        self.r = player.yaw

    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, 0)
        glRotatef(-self.r+180, 0, 0, 1)
        glScalef(1/self.window.scale, 1/self.window.scale, 1)
        glScalef(2, 2, 1)
        for part in self.parts:
            part.draw()
        glPopMatrix()


class PortalIndicator(object):
    def __init__(self, window, region_x, region_z, chunk_x, chunk_z):
        region_width = 32*16
        # Get the center of the target chunk
        self.window = window
        self.x = region_width*region_x+8+16*(chunk_x+1)
        self.y = -region_width*(region_z+1)+8+16*(chunk_z+1)
        self.parts = [
            pyglet.shapes.Rectangle(-2, -3, 4, 6, color=tuple(block_colors["nether_portal"])),
            pyglet.shapes.Line(-2, 3, 2, 3, 1, color=(0,0,0)),
            pyglet.shapes.Line(-2, 3, -2, -3, 1, color=(0,0,0)),
            pyglet.shapes.Line(2, -3, -2, -3, 1, color=(0,0,0)),
            pyglet.shapes.Line(2, -3, 2, 3, 1, color=(0,0,0)),
        ]

    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, 0)
        glScalef(1/self.window.scale, 1/self.window.scale, 1)
        glScalef(4, 4, 1)
        for part in self.parts:
            part.draw()
        glPopMatrix()


class MapViewerWindow(pyglet.window.Window):
    def __init__(self, world, *args, **kwargs):
        pyglet.window.Window.__init__(self, *args, **kwargs)
        self.level = world
        self._player = None
        self._dimension = None
        self.indicator = Indicator(self)
        self.dimension = None
        self.scale = 2.0
        # Some additional attributes will be set by player.setter
        self.player = self.level.get_players()[0]
        self.sprite_lock = threading.Lock()
        self.locate_player()
        self.gui = self.setup_gui()
        self.progress_lock = threading.Lock()
        self.set_progress(None)
        self.cancel_render = False
        pyglet.clock.schedule_interval(self.on_draw, 0.25)
        self.workers = []
        self.render_thread = None
        # self.render_thread = threading.Thread(target=self.render_world)
        # self.render_thread.start()
        self.portal = PortalIndicator(self, 0, 0, 12, 20)

    @property
    def player(self):
        return self._player

    @player.setter
    def player(self, value):
        self._player = value
        if value.dimension != self.dimension:
            self.dimension = value.dimension
            self.locate_player()
        self.player_location = (value.x, value.z)
        self.indicator.update(value)

    @property
    def dimension(self):
        return self._dimension

    @dimension.setter
    def dimension(self, value):
        self._dimension = value
        self.sprites = SpriteManager(fs.get_data_dir(self.level.folder), value)
        self.set_caption(f"Map Viewer - {self.level.name} - {self._dimension}")

    def locate_player(self):
        self.x = self._player.x-self.width/(2*self.scale)
        self.y = -self._player.z-self.height/(2*self.scale)

    def setup_gui(self):
        self.font_spacing = None
        btn_height = None
        self.gui = []
        self.button_regions = {}
        self.rectangles = {}
        self.pressed_button = None
        y = 0
        for text in ("REFRESH MAP", "LOCATE PLAYER", "CHANGE DIMENSION", "FIND PORTALS"):
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

    def set_progress(self, progress):
        with self.progress_lock:
            self.progress = progress

    def render_world(self):
        if len(self.workers) > 0:
            return
        self.set_progress(("Checking regions...", (0, 100)))
        dimension = self.dimension
        region_files = self.level.get_regions(dimension)
        regions = []
        for filename in region_files:
            parts = os.path.basename(filename).split(".")
            regions.append((int(parts[1]), int(parts[2])))
        data_dir = fs.get_data_dir(self.level.folder)
        renderable_regions = []
        for idx, region in enumerate(regions):
            self.set_progress(("Checking regions...", (idx, len(regions))))
            x, z = region
            try:
                region = self.level.get_region(dimension, x, z)
            except Exception as e:
                print("\n%s" % e)
                continue
            tile_file = os.path.join(data_dir, "%s.%s.%s.png" % (dimension, x, z))
            if not os.path.isfile(tile_file) or os.path.getmtime(tile_file) < os.path.getmtime(region.filename):
                renderable_regions.append((tile_file, x, z))
        self.set_progress(("Checking regions...", (1, 1)))

        all_missing_blocks = set()
        def _render_region(filename, region_x, region_z):
            if self.cancel_render:
                return
            command = [sys.executable, __file__, self.level.folder,
                "--region", f" {region_x},{region_z}", "--dimension", dimension]
            kwargs = {"stdout":subprocess.PIPE, "stderr":subprocess.STDOUT}
            # if os.name == "nt":
            #     kwargs["creationflags"] = 0x08000000 # CREATE_NO_WINDOW
            print(f"Rendering region {command[-1]} {kwargs}")
            worker = subprocess.Popen(command, **kwargs)
            output = worker.communicate()[0]
            if output:
                output = output.decode(sys.stdout.encoding or "utf-8")
                for line in output.splitlines():
                    if line.startswith("Missing block: "):
                        all_missing_blocks.add(line.replace("Missing block: ", ""))
            self.workers.append(worker)
            if worker.wait() == 0:
                with self.sprite_lock:
                    self.sprites.sprites[(region_x, region_z)] = filename
            else:
                print(output)

        if len(renderable_regions) > 0:
            self.set_progress((f"Rendering {len(renderable_regions)} regions...", (0, len(renderable_regions))))
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = [executor.submit(_render_region, *info) for info in renderable_regions]
                for idx, future in enumerate(concurrent.futures.as_completed(futures), 1):
                    self.set_progress((f"Rendering {len(renderable_regions)} regions...", (idx, len(renderable_regions))))
                    e = future.exception()
                    if e:
                        print(e)
        if all_missing_blocks:
            print("Missing blocks:\n  "+"\n  ".join(sorted(all_missing_blocks)))

        def _clear_progress(*args, **kwargs):
            self.set_progress(None)
        pyglet.clock.schedule_once(_clear_progress, 1, None)
        self.workers = []
        self.render_thread = None

    def find_portals(self):
        self.set_progress(("Finding portals...", (0, 1)))
        regions = []
        for dimension in ("overworld", "nether"):
            for filename in self.level.get_regions(dimension):
                parts = os.path.basename(filename).split(".")
                regions.append((dimension, int(parts[1]), int(parts[2])))
        data_dir = fs.get_data_dir(self.level.folder)

        portals = []
        region_idx = 0
        def _process_region(dt):
            nonlocal region_idx
            if region_idx == len(regions):
                with open(os.path.join(data_dir, "portals.json"), "w") as f:
                    f.write(json.dumps(portals))
                pyglet.clock.unschedule(_process_region)
                self.set_progress(None)
                self.portals = portals
            try:
                dimension, region_x, region_z = regions[region_idx]
            except IndexError as e:
                print(f"{e}: len(regions)={len(regions)}, region_idx={region_idx}")
                return
            region = self.level.get_region(dimension, region_x, region_z)
            for x in range(32):
                for z in range(32):
                    try:
                        chunk = region.get_chunk(x, z)
                    except nbt.region.InconceivedChunk:
                        continue
                    for section in chunk["Level"]["Sections"]:
                        if "Palette" not in section:
                            continue
                        if any(b["Name"].value == "minecraft:nether_portal" for b in section["Palette"]):
                            portals.append(regions[region_idx]+(x, z))
            region_idx += 1
            self.set_progress(("Finding portals...", (region_idx, len(regions))))
        pyglet.clock.schedule(_process_region)

    def on_key_press(self, key, modifiers):
        if key == KEY.ESCAPE:
            self.minimize()
            return pyglet.event.EVENT_HANDLED

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

    def on_activate(self):
        new_player = self.level.get_players()[0]
        if self.dimension == new_player.dimension:
            self.player = new_player

    def on_draw(self, dt=None):
        # starttime = time.time()
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
        if self.dimension == self.player.dimension:
            self.indicator.draw()
        self.portal.draw()

        glLoadIdentity()
        glTranslatef(0, self.height, 0)
        for item in self.gui:
            item.draw()

        with self.progress_lock:
            if self.progress:
                glLoadIdentity()
                pyglet.shapes.Rectangle(0, 0, self.width, 3*self.font_height+self.font_spacing, color=(192,192,192)).draw()
                pyglet.shapes.Line(0, 3*self.font_height+self.font_spacing, self.width, 3*self.font_height+self.font_spacing, 5, color=(0,0,0)).draw()
                pyglet.shapes.Rectangle(self.font_spacing, self.font_spacing,
                    self.width-2*self.font_spacing, self.font_height, color=(255,255,255)).draw()
                progress_width = self.progress[1][0] / self.progress[1][1] * (self.width-2*self.font_spacing)
                pyglet.shapes.Rectangle(self.font_spacing, self.font_spacing,
                    progress_width, self.font_height, color=(64, 255, 64)).draw()
                pyglet.text.Label(self.progress[0].upper(), bold=True, x=self.font_spacing, y=self.font_height*2+self.font_spacing,
                    anchor_y="center", color=(0,0,0,255)).draw()

        # duration = time.time()-starttime
        # print(f"\r{duration:.3f}", end="")

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self.pressed_button:
            return
        self.x -= dx/self.scale
        self.y -= dy/self.scale

    def on_mouse_press(self, x, y, button, modifiers):
        for region, command in self.button_regions.items():
            xMin, yMin, xMax, yMax = region
            if xMin < x < xMax and yMin < y-self.height < yMax:
                self.pressed_button = command
                self.rectangles[command].color = (255,255,255)

    def on_mouse_release(self, x, y, button, modifiers):
        for region, command in self.button_regions.items():
            xMin, yMin, xMax, yMax = region
            if command == self.pressed_button and xMin < x < xMax and yMin < y-self.height < yMax:
                if command == "REFRESH MAP":
                    if not self.render_thread:
                        self.render_thread = threading.Thread(target=self.render_world)
                        self.render_thread.start()
                elif command == "LOCATE PLAYER":
                    self.player = self.level.get_players()[0]
                    self.locate_player()
                elif command == "CHANGE DIMENSION":
                    dimensions = {"overworld":"nether","nether":"end","end":"overworld"}
                    self.dimension = dimensions[self.dimension]
                    self.sprites = SpriteManager(fs.get_data_dir(self.level.folder), self.dimension)
                elif command == "FIND PORTALS":
                    self.find_portals()

        if self.pressed_button:
            self.rectangles[self.pressed_button].color = (192, 192, 192)
            self.pressed_button = None

        # Select a chunk for debugging
        if modifiers & 2: # CTRL is pressed
            print("mouse click:", (x, y))
            world_x = self.x + (self.width*(x/self.width)/self.scale)
            world_z = -(self.y + (self.height*(y/self.height)/self.scale))
            region_x = int(world_x // 512)
            region_z = int(world_z // 512)
            region_origin_x = region_x * 512
            region_origin_z = region_z * 512
            chunk_x = (world_x - region_origin_x) // 16
            chunk_z = (world_z - region_origin_z) // 16
            chunk = self.level.get_region("overworld", region_x, region_z).get_chunk(chunk_x, chunk_z)
            print((world_x, world_z), (region_x, region_z), (chunk_x, chunk_z))
            binn = lambda i: ("%64s" % bin(i).replace("-", "")[2:]).replace(" ", "0")
            # print("Heightmap:")
            # print("\n".join(binn(e) for e in chunk["Level"]["Heightmaps"]["WORLD_SURFACE"]))
            # sea level section
            section = next(section for section in chunk["Level"]["Sections"] if section["Y"].value == 3)
            print("Palette:")
            print("\n".join(str(e) for e in section["Palette"]))
            # print("Blocks:")
            # print("\n".join(binn(e) for e in section["BlockStates"]))
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
    parser.add_argument("--dimension", default="overworld",
        choices=("overworld", "nether", "end"),
        help="Which dimension to process")
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
        render_world(args.world.folder, args.dimension)
        if len(missing_blocks):
            print("Missing blocks:")
            print("  " + "\n  ".join(sorted(missing_blocks.keys())))
    elif args.region:
        x, z = map(int, args.region.strip().split(","))
        data_dir = fs.get_data_dir(args.world.folder)
        filename = os.path.join(data_dir, f"{args.dimension}.{x}.{z}.png")
        if args.dimension == "nether":
            # Render a horizontal slice of the nether at the surface of the lava lake
            render_region(args.world.get_region(args.dimension, x, z), 31).save(filename)
        else:
            render_region(args.world.get_region(args.dimension, x, z)).save(filename)
        if len(missing_blocks):
            print("\n".join(f"Missing block: {b}" for b in sorted(missing_blocks)))
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
