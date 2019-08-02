#!/usr/bin/env python3

import pyglet
from pyglet.gl import *

class MapViewerWindow(pyglet.window.Window):
    def __init__(self, *args, **kwargs):
        pyglet.window.Window.__init__(self, *args, **kwargs)
        self.image = pyglet.image.load("test.png")
        self.sprite = pyglet.sprite.Sprite(img=self.image)
        self.scale = 1.0
        self.x = 0.0
        self.y = 0.0

    def on_draw(self):
        self.clear()
        glLoadIdentity()
        glScalef(self.scale, self.scale, self.scale)
        glTranslatef(self.x, self.y, 0)
        self.sprite.draw()

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self.x += dx/self.scale
        self.y += dy/self.scale

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        # previous = self.scale

        self.scale *= pow(1.1, scroll_y)
        # zoom in (+scroll_y) => x should decrease

    def on_mouse_release(self, x, y, button, modifiers):
        mouse_x = self.x + (x/self.scale)
        mouse_y = self.y + (y/self.scale)
        print(tuple(map(int, (self.x, self.y))), ": ", tuple(map(int, (x, y))), "->", tuple(map(int, (mouse_x, mouse_y))))
        # before doing any scaling, clicking the top right of the test image should always yield 400,300

if __name__ == '__main__':
    window = MapViewerWindow(resizable=True)
    pyglet.app.run()
