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
    'acacia_leaves':            (27,    92,     20),
    'acacia_log':               (147,   88,     5),
    'air':                      (0,     0,      0),
    'andesite':                 (81,    81,     81),
    'azure_bluet':              (255,   255,    255),
    'bedrock':                  (25,    25,     25),
    'birch_leaves':             (27,    92,     20),
    'birch_log':                (147,   88,     5),
    'blue_orchid':              (255,   255,    255),
    'bookshelf':                (255,   255,    255),
    'brown_mushroom':           (255,   255,    255),
    'brown_mushroom_block':     (255,   255,    255),
    'cactus':                   (19,    82,     26),
    'cave_air':                 (0,     0,      0),
    'chest':                    (255,   0,      0),
    'clay':                     (95,    30,     22),
    'coal_ore':                 (25,    25,     25),
    'cobblestone':              (63,    63,     63),
    'cobblestone_stairs':       (63,    63,     63),
    'crafting_table':           (255,   255,    255),
    'dandelion':                (254,   255,    50),
    'dark_oak_leaves':          (27,    92,     20),
    'dark_oak_log':             (147,   88,     5),
    'dark_oak_planks':          (147,   88,     5),
    'dead_bush':                (255,   255,    255),
    'diorite':                  (81,    81,     81),
    'dirt':                     (57,    36,     18),
    'end_portal_frame':         (255,   0,      0),
    'farmland':                 (73,    44,     2),
    'fire':                     (255,   233,    0),
    'flowing_lava':             (244,   65,     0),
    'flowing_water':            (29,    41,     87),
    'glass_pane':               (255,   255,    255),
    'granite':                  (81,    81,     81),
    'grass':                    (60,    90,     36),
    'grass_block':              (77,    115,    47),
    'gravel':                   (60,    48,     41),
    'ice':                      (240,   240,    243),
    'infested_stone':           (255,   0,      169),
    'iron_bars':                (220,   138,    90),
    'iron_ore':                 (220,   138,    90),
    'ladder':                   (147,   88,     5),
    'lava':                     (244,   65,     0),
    'lilac':                    (255,   255,    255),
    'lily_pad':                 (22,    75,     16),
    'lit_pumpkin':              (229,   91,     0),
    'mossy_cobblestone':        (95,    165,    89),
    'mushroom_stem':            (255,   255,    255),
    'oak_door':                 (147,   88,     5),
    'oak_fence':                (147,   88,     5),
    'oak_fence_gate':           (147,   88,     5),
    'oak_leaves':               (27,    92,     20),
    'oak_log':                  (147,   88,     5),
    'oak_planks':               (147,   88,     5),
    'oak_pressure_plate':       (147,   88,     5),
    'oak_stairs':               (27,    92,     20),
    'peony':                    (255,   255,    255),
    'pink_tulip':               (0,     0,      0),
    'poppy':                    (255,   0,      0),
    'pumpkin':                  (229,   91,     0),
    'rail':                     (230,   137,    24),
    'red_mushroom':             (76,    25,     25),
    'red_mushroom_block':       (76,    25,     25),
    'rose_bush':                (255,   255,    255),
    'sand':                     (171,   165,    124),
    'sandstone':                (133,   120,    70),
    'seagrass':                 (60,    90,     36),
    'sign':                     (27,    92,     20),
    'snow':                     (212,   212,    220),
    'spawner':                  (0,     254,    255),
    'spruce_leaves':            (27,    92,     20),
    'spruce_log':               (147,   88,     5),
    'stone':                    (81,    81,     81),
    'stone_slab':               (81,    81,     81),
    'sugar_cane':               (38,    216,    47),
    'tall_grass':               (60,    90,     36),
    'tall_seagrass':            (60,    90,     36),
    'torch':                    (254,   255,    0),
    'vine':                     (22,    75,     16),
    'wall_torch':               (254,   255,    0),
    'water':                    (29,    41,     87),
    'wheat':                    (50,    204,    58),
    'white_wool':               (255,   255,    255),
    }

missing_blocks = {}

def get_map(chunk):
    # Show an image of the chunk from above

    try:
        heightmap = chunk["Level"]["Heightmaps"]["WORLD_SURFACE"]
    except:
        # If the heightmap isn't included, just return a black square
        return Image.frombytes("RGB", (16, 16),
            b"".join(bytes((0, 0, 0)) for _ in range(256)))
    # Heightmap is a list of longs, convert them into one string of bytes
    hytes = b"".join(val.to_bytes(8, "little", signed=True) for val in heightmap)
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
            color = block_colors.get(block)
            if not color:
                # Magenta for types that aren't in there yet
                missing_blocks[block] = True
                pixels.append(bytes((255, 0, 255)))
            else:
                pixels.append(bytes(color))

    return Image.frombytes("RGB", (16, 16), b"".join(pixels))


def main():
    parser = argparse.ArgumentParser("Minecraft map generator")
    parser.add_argument("folder", help="A Minecraft save folder")
    parser.add_argument("--show", action="store_true", help="Open the map upon completion")
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
            chunkmap = get_map(chunk)
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
