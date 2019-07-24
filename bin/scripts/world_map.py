#!/usr/bin/env python
"""
Prints a map of the entire world.
"""

import argparse
import os

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


# Map of block colors from names
# Legacy block numeric identifiers are now hidden by Block class
# and mapped to alpha identifiers in best effort
# TODO: move this map into a separate config file

block_colors = {
    'air':                      bytes((0, 0, 0)),

    'andesite':                 bytes((138, 138, 142)),
    'azure_bluet':              bytes((85, 171, 45)),
    'birch_leaves':             bytes((112, 109, 112)),
    'blue_orchid':              bytes((39, 169, 244)),
    'brown_mushroom':           bytes((204, 153, 120)),
    'cactus':                   bytes((82, 125, 38)),
    'coal_ore':                 bytes((127, 127, 127)),
    'dandelion':                bytes((255, 236, 79)),
    'dark_oak_leaves':          bytes((183, 185, 183)),
    'dark_oak_log':             bytes((63, 49, 29)),
    'dead_bush':                bytes((81, 61, 36)),
    'diorite':                  bytes((233, 233, 233)),
    'dirt':                     bytes((121, 85, 58)),
    'granite':                  bytes((159, 107, 88)),
    'grass':                    bytes((160, 160, 160)),
    'grass_block':              bytes((151, 151, 151)),
    'gravel':                   bytes((129, 127, 127)),
    'ice':                      bytes((146, 185, 254)),
    'iron_ore':                 bytes((127, 127, 127)),
    'lava':                     bytes((209, 79, 12)),
    'lilac':                    bytes((211, 128, 211)),
    'lily_pad':                 bytes((150, 150, 150)),
    'oak_leaves':               bytes((152, 153, 152)),
    'oak_log':                  bytes((116, 90, 54)),
    'peony':                    bytes((235, 197, 253)),
    'poppy':                    bytes((237, 48, 44)),
    'rail':                     bytes((103, 80, 44)),
    'red_mushroom':             bytes((226, 18, 18)),
    'rose_bush':                bytes((191, 37, 41)),
    'sand':                     bytes((218, 207, 163)),
    'sandstone':                bytes((227, 219, 176)),
    'seagrass':                 bytes((47, 130, 0)),
    'snow':                     bytes((255, 255, 255)),
    'stone':                    bytes((127, 127, 127)),
    'sugar_cane':               bytes((130, 168, 89)),
    'tall_grass':               bytes((172, 170, 172)),
    'tall_seagrass':            bytes((56, 147, 6)),
    'torch':                    bytes((159, 127, 80)),
    'vine':                     bytes((131, 131, 131)),
    'wall_torch':               bytes((159, 127, 80)),
    'water':                    bytes((165, 165, 165)),
    'wheat':                    bytes((166, 149, 83)),

    'beetroots':                bytes((116, 35, 3)),
    'bell':                     bytes((123, 94, 13)),
    'birch_sapling':            bytes((108, 158, 56)),
    'blue_ice':                 bytes((108, 163, 253)),
    'blue_terracotta':          bytes((74, 59, 91)),
    'brown_terracotta':         bytes((77, 52, 36)),
    'bubble_column':            bytes((165, 165, 165)),
    'chiseled_stone_bricks':    bytes((90, 89, 90)),
    'cornflower':               bytes((87, 140, 77)),
    'cracked_stone_bricks':     bytes((127, 127, 127)),
    'cut_sandstone':            bytes((218, 210, 163)),
    'dark_oak_sapling':         bytes((16, 82, 16)),
    'dark_oak_slab':            bytes((79, 50, 24)),
    'glass':                    bytes((208, 234, 233)),
    'gold_ore':                 bytes((127, 127, 127)),
    'hay_block':                bytes((171, 146, 37)),
    'jungle_button':            bytes((184, 135, 100)),
    'kelp':                     bytes((89, 171, 48)),
    'light_gray_terracotta':    bytes((135, 107, 98)),
    'lily_of_the_valley':       bytes((55, 127, 19)),
    'melon_stem':               bytes((177, 177, 177)),
    'mossy_stone_bricks':       bytes((127, 127, 127)),
    'orange_terracotta':        bytes((159, 82, 36)),
    'oxeye_daisy':              bytes((247, 247, 247)),
    'packed_ice':               bytes((146, 185, 254)),
    'potted_cactus':            bytes((137, 76, 59)),
    'red_sand':                 bytes((191, 103, 33)),
    'red_terracotta':           bytes((141, 59, 46)),
    'sandstone_slab':           bytes((227, 219, 176)),
    'sandstone_stairs':         bytes((227, 219, 176)),
    'smooth_sandstone':         bytes((227, 219, 176)),
    'smooth_sandstone_slab':    bytes((227, 219, 176)),
    'smooth_sandstone_stairs':  bytes((227, 219, 176)),
    'snow_block':               bytes((255, 255, 255)),
    'stone_brick_stairs':       bytes((127, 127, 127)),
    'stone_bricks':             bytes((127, 127, 127)),
    'terracotta':               bytes((150, 93, 67)),
    'white_terracotta':         bytes((210, 177, 161)),
    'yellow_terracotta':        bytes((184, 131, 34)),

    }

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
