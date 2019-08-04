#!/usr/bin/env python3

import argparse
import os
import pyglet
from pyglet.gl import *


class MapViewerWindow(pyglet.window.Window):
    def __init__(self, image, *args, **kwargs):
        pyglet.window.Window.__init__(self, *args, **kwargs)
        self.image = pyglet.image.load(image)
        self.sprite = pyglet.sprite.Sprite(img=self.image)
        self.scale = 1.0
        self.x = 0
        self.y = 0
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

    def on_draw(self):
        self.clear()
        glLoadIdentity()
        glScalef(self.scale, self.scale, 1)
        glTranslatef(self.x, self.y, 0)
        self.sprite.draw()

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self.x += dx/self.scale
        self.y += dy/self.scale

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        mouse_x = x/self.scale - self.x
        mouse_y = y/self.scale - self.y
        self.scale *= pow(1.1, scroll_y)
        self.x = x/self.scale - mouse_x
        self.y = y/self.scale - mouse_y


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("filename")
    args = parser.parse_args()

    window = MapViewerWindow(args.filename,
        resizable=True, width=1024, height=768, caption="Map Viewer")
    pyglet.app.run()


if __name__ == '__main__':
    main()
