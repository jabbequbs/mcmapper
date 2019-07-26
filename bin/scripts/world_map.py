#!/usr/bin/env python
"""
Prints a map of the entire world.
"""

import argparse
import os

from mapper import block_colors
from nbt.world import WorldFolder
from PIL import Image


# List of blocks to ignore
# Uncomment all the lines to show underground structures
# TODO: move this list into a separate config file

block_ignore = [
    'air',  # At least this one
#    'cave_air', 'water', 'lava', 'snow', 'ice',
#    'grass', 'tall_grass', 'dead_bush',
#    'seagrass', 'tall_seagrass', 'kelp', 'kelp_plant',
#    'dandelion', 'poppy', 'oxeye_daisy', 'white_tulip',
#    'azure_bluet', 'lilac', 'rose_bush', 'peony', 'blue_orchid',
#    'lily_pad', 'sugar_cane', 'vine', 'pumpkin', 'cactus',
#    'wheat', 'potatoes', 'beetroots', 'carrots',
#    'oak_leaves', 'dark_oak_leaves', 'birch_leaves',
#    'acacia_leaves', 'spruce_leaves',
#    'oak_log', 'dark_oak_log', 'birch_log',
#    'acacia_log', 'spruce_log',
#    'brown_mushroom', 'red_mushroom',
#    'brown_mushroom_block', 'red_mushroom_block', 'mushroom_stem',
#    'grass_block', 'grass_path', 'farmland', 'dirt',
#    'stone', 'sand', 'gravel', 'clay',
#    'sandstone', 'diorite', 'andesite', 'granite', 'obsidian',
#    'coal_ore', 'iron_ore', 'gold_ore', 'diamond_ore',
#    'redstone_ore', 'lapis_ore', 'emerald_ore',
#    'cobweb',
    ]

missing_blocks = {}

def get_map(chunk, layer, heightmap=False):
    # Show an image of the chunk from above

    try:
        height_data = chunk["Level"]["Heightmaps"][layer]
    except:
        # If the heightmap isn't included, just return a black square
        return Image.frombytes("RGB", (16, 16),
            b"".join(bytes((0, 0, 0)) for _ in range(256)))
    # Heightmap is a list of longs, convert them into one string of bytes
    hytes = b"".join(val.to_bytes(8, "little", signed=True) for val in height_data)
    # Convert the string of bytes into a string of bits.  This changes it from little to big endian
    strytes = ("%*s" % (256*9, bin(int.from_bytes(hytes, "little"))[2:])).replace(" ", "0")
    # Chop the bitstring into integers of nine bits each, and then reverse
    # the whole thing to get back to little endian
    heights = [int(strytes[i:i+9], base=2)-1 for i in range(0, 256*9, 9)][::-1]

    pixels = []
    sections = {}
    for z in range(16):
        for x in range(16):
            pixel_idx = z*16+x
            if heightmap:
                pixels.append(bytes((heights[pixel_idx], heights[pixel_idx], heights[pixel_idx])))
                continue
            section_y = heights[pixel_idx] // 16
            if section_y not in sections:
                try:
                    section = next(section for section in chunk["Level"]["Sections"]
                        if section["Y"].value == section_y)
                except:
                    section = next(section for section in reversed(chunk["Level"]["Sections"])
                        if "Palette" in section)
                # Find the number of bits it takes to represent the largest index in the palette (at least 4)
                try:
                    index_len = max((4, len(bin(len(section["Palette"])-1)[2:])))
                except KeyError:
                    # print((chunk["Level"]["xPos"].value, chunk["Level"]["zPos"].value), heights[pixel_idx])
                    # raise
                    pixels.append(bytes((255, 255, 255)))
                    continue
                # BlockStates is a list of longs, convert them into one string of bytes
                blockstates = b"".join(val.to_bytes(8, "little", signed=True) for val in section["BlockStates"])
                # Convert the string of bytes into a string of bits.  This changes it from little to big endian
                # Each long in BlockStates will be 64 bits long
                bits = ("%*s" % (64*len(section["BlockStates"]), bin(int.from_bytes(blockstates, "little"))[2:])).replace(" ", "0")
                # Get the list of palette indexes and reverse it to compensate for big endianness
                blocks = [int(bits[i:i+index_len], base=2) for i in range(0, 4096*index_len, index_len)][::-1]
                sections[section_y] = (section, blocks)
            section, blocks = sections[section_y]
            palette_idx = blocks[(heights[pixel_idx]%16)*256+z*16+x]
            block = section["Palette"][palette_idx]["Name"].value.replace("minecraft:", "")
            if block not in block_colors:
                missing_blocks[block] = True
                color = block_colors["air"]
            else:
                color = block_colors[block]
            pixels.append(color)

    return Image.frombytes("RGB", (16, 16), b"".join(pixels))


def main():
    parser = argparse.ArgumentParser("Minecraft map generator")
    parser.add_argument("folder", help="A Minecraft save folder")
    parser.add_argument("--show", action="store_true", help="Open the map upon completion")
    parser.add_argument("--heightmap", action="store_true", help="Render a heightmap")
    parser.add_argument("--layer", choices=("WORLD_SURFACE", "OCEAN_FLOOR"),
        default="WORLD_SURFACE", help="Which heightmap to use")
    args = parser.parse_args()

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
            chunkmap = get_map(chunk, args.layer, args.heightmap)
            x = chunk["Level"]["xPos"].value
            z = chunk["Level"]["zPos"].value
            world_map.paste(chunkmap, (16*(x-bb.minx),16*(z-bb.minz)))
        print("\rGenerating map... 100.0%")
        if len(missing_blocks):
            print("Missing blocks:")
            print("  " + "\n  ".join(sorted(missing_blocks.keys())))
        filename = os.path.basename(args.folder)+".png"
        world_map.save(filename,"PNG")
        print("Saved map as %s" % filename)
    except KeyboardInterrupt:
        print(" aborted\n")
        filename = os.path.basename(args.folder)+".partial.png"
        world_map.save(filename,"PNG")
        print("Saved map as %s" % filename)
        return 75 # EX_TEMPFAIL
    if args.show:
        world_map.show()
    return 0 # NOERR

if __name__ == '__main__':
    main()
