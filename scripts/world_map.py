#!/usr/bin/env python
"""
Prints a map of the entire world.
"""

import argparse
import os

from mcmapper.mapper import render_world, missing_blocks


def main():
    parser = argparse.ArgumentParser("Minecraft map generator")
    parser.add_argument("folder", help="A Minecraft save folder")
    parser.add_argument("filename", help="The image file to create")
    parser.add_argument("--show", action="store_true", help="Open the map upon completion")
    parser.add_argument("--heightmap", action="store_true", help="Render a heightmap")
    parser.add_argument("--layer", choices=("WORLD_SURFACE", "OCEAN_FLOOR"),
        default="WORLD_SURFACE", help="Which heightmap to use")
    args = parser.parse_args()

    if not args.filename.endswith(".png"):
        args.filename += ".png"

    if not os.path.isdir(args.folder):
        minecraft_saves = os.path.join(os.environ["APPDATA"], ".minecraft", "saves")
        worlds = [f for f in os.listdir(minecraft_saves)
            if os.path.isdir(os.path.join(minecraft_saves, f))]
        if args.folder in worlds:
            args.folder = os.path.join(minecraft_saves, args.folder)
        else:
            sys.exit("%s: invalid world.  Options are %s" % (args.folder, worlds))

    result = render_world(args.folder)
    if len(missing_blocks):
        print("Missing blocks:")
        print("  " + "\n  ".join(sorted(missing_blocks.keys())))
    print("Saving image...")
    result.save(args.filename, "PNG")
    print("Done")


if __name__ == '__main__':
    main()