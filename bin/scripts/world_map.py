#!/usr/bin/env python
"""
Prints a map of the entire world.
"""

import argparse
import os

from mapper import render_chunk, missing_blocks
from nbt.world import WorldFolder
from PIL import Image


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

    print("Opening world...")
    world = WorldFolder(args.folder)
    print("Getting bounding box...")
    bb = world.get_boundingbox()
    print("Generating image placeholder...")
    world_map = Image.new('RGB', (16*bb.lenx(),16*bb.lenz()))
    print("Getting world chunk count...")
    t = world.chunk_count()
    try:
        i = 0.0
        print("Generating map...   0.0%", end="", flush=True)
        print("\b\b\b\b\b\b%5s%%" % ("%.1f" % (100*i/t)), end="", flush=True)
        for chunk in world.iter_nbt():
            # assert chunk["DataVersion"].value == 1976
            if i % 50 ==0:
                print("\b\b\b\b\b\b%5s%%" % ("%.1f" % (100*i/t)), end="", flush=True)
            i +=1
            chunkmap = render_chunk(chunk, args.layer, args.heightmap)
            x = chunk["Level"]["xPos"].value
            z = chunk["Level"]["zPos"].value
            world_map.paste(chunkmap, (16*(x-bb.minx),16*(z-bb.minz)))
        print("\rGenerating map... 100.0%")
        if len(missing_blocks):
            print("Missing blocks:")
            print("  " + "\n  ".join(sorted(missing_blocks.keys())))
        world_map.save(args.filename,"PNG")
        print("Saved map as %s" % args.filename)
    except KeyboardInterrupt:
        print(" aborted\n")
        filename = "%s.partial%s" % os.path.splitext(args.filename)
        world_map.save(filename,"PNG")
        print("Saved map as %s" % filename)
        return 75 # EX_TEMPFAIL
    if args.show:
        world_map.show()
    return 0 # NOERR

if __name__ == '__main__':
    main()
