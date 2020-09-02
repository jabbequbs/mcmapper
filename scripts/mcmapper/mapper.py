import nbt
import os

from .data import map_colors, block_colors
from .filesystem import get_data_dir
from .level import LevelInfo, dimensions
from PIL import Image


def render_map(filename, verbose=False):
    log = lambda message: None
    if verbose:
        log = print

    log("Loading file...")
    data = nbt.nbt.NBTFile(filename)
    log("Map version %s" % data["DataVersion"].value)
    colors_idxs = map_colors.get(data["DataVersion"].value, map_colors[0])
    colors = data["data"]["colors"].value
    pixels = []
    missing = {}
    log("Generating pixels...")
    for z in range(128):
        for x in range(128):
            idx = z*128+x
            color = colors_idxs.get(colors[idx])
            # color = bytes((colors[idx], colors[idx], colors[idx]))
            if not color:
                missing[colors[idx]] = True
                color = bytes((colors[idx], colors[idx], colors[idx]))
            pixels.append(color)

    if len(missing):
        log("Missing color indexes:\n  " + "\n  ".join(map(str, sorted(missing.keys()))))

    log("Generating image...")
    return Image.frombytes("RGB", (128, 128), b"".join(pixels))


missing_blocks = {}
def render_chunk(chunk, layer, heightmap=False):
    # Show an image of the chunk from above
    try:
        height_data = chunk["Level"]["Heightmaps"][layer]
    except:
        # If the heightmap isn't included, just return a black square
        return Image.frombytes("RGB", (16, 16),
            b"".join(bytes((0, 0, 0)) for _ in range(256)))
    if len(height_data) == 36: # Pre Minecraft 1.16
        # Convert the heightmap (a list of longs) into a bitstring.  There's some endian weirdness, so the list
        # of longs is reversed first.
        bitstring = "".join(("%64s" % bin(h)[2:]).replace(" ", "0") for h in height_data)
        # Chop the bitstring into integers of nine bits each, and then reverse
        # the whole thing to get back to little endian.
        # Subtract one from the height to get the block underneath it.
        heights = [int(bitstring[i:i+9], base=2)-1 for i in range(0, 256*9, 9)][::-1]
    else:
        # In 1.16 and up, heightmaps are 37 longs, each with 7 values of 9 bits.  The last bit of each long
        # is unused (7*9 = 63), and the last 28 bits of the last long.
        # The heightmap for an ocean chunk looks like this:
        #   01: 0000111111000111111000111111000111111000111111000111111000111111
        #   02: 0000111111000111111000111111000111111000111111000111111000111111
        #   03: 0000111111000111111000111111000111111000111111000111111000111111
        #   ...
        #   37: 0000000000000000000000000000000111111000111111000111111000111111
        heights = []
        for h in height_data:
            bits = ("%64s" % bin(h).replace("-", "")[2:]).replace(" ", "0")
            heights.extend(int(bits[i-9:i], base=2)-1 for i in range(64, 1, -9))

    black = bytes((0, 0, 0))
    pixels = []
    sections = {}
    debug_distinct_blocks = {}
    for z in range(16):
        for x in range(16):
            pixel_idx = z*16+x
            if heightmap:
                pixels.append(bytes((heights[pixel_idx], heights[pixel_idx], heights[pixel_idx])))
                continue
            section_y = heights[pixel_idx] // 16
            if section_y not in sections:
                if len(chunk["Level"]["Sections"]) == 0 or section_y == -1:
                    pixels.append(black)
                    continue
                # try:
                section = next(section for section in chunk["Level"]["Sections"]
                    if section["Y"].value == section_y)
                # except StopIteration:
                #     try:
                #         section = next(section for section in reversed(chunk["Level"]["Sections"])
                #             if "Palette" in section)
                #     except StopIteration:
                #         raise Exception("Weird sections (was looking for %s): %s" % (section_y, [c.tags for c in chunk["Level"]["Sections"]]))
                # Find the number of bits it takes to represent the largest index in the palette (at least 4)
                try:
                    index_len = max((4, len(bin(len(section["Palette"])-1))-2))
                except KeyError:
                    pixels.append(black)
                    continue
                # BlockStates is a list of longs, each of which has some number of indices
                # Many ocean chunks will have 16 zeros terminating the list of longs
                blocks = []
                for idx, bs in enumerate(section["BlockStates"]):
                    bits = ("%64s" % bin(bs).replace("-", "")[2:]).replace(" ", "0")
                    # Take slices of size index_len bits from the right hand side
                    blocks.extend(int(bits[i-index_len:i], base=2) for i in range(64, index_len-1, -index_len))
                sections[section_y] = (section, blocks)

            # Get the chunk section and block states
            section, blocks = sections[section_y]
            # The block state is an index into the palette
            palette_idx = blocks[(heights[pixel_idx]%16)*256+z*16+x]
            debug_distinct_blocks[(section_y, palette_idx)] = True
            try:
                block = section["Palette"][palette_idx]["Name"].value.replace("minecraft:", "")
            except IndexError:
                color = block_colors["magenta_concrete"]
            else:
                if block not in block_colors:
                    missing_blocks[block] = True
                    color = block_colors["magenta_concrete"]
                else:
                    color = block_colors[block]
            pixels.append(color)

    return Image.frombytes("RGB", (16, 16), b"".join(pixels))


def render_region(region):
    result = Image.new("RGB", (32*16, 32*16))
    for x in range(32):
        for z in range(32):
            try:
                chunk = region.get_chunk(x, z)
            except nbt.region.InconceivedChunk:
                pass
            else:
                result.paste(render_chunk(chunk, "WORLD_SURFACE"), (x*16, z*16))
    return result


def render_world(world):
    print("Loading world...")
    if type(world) is str:
        world = LevelInfo(world)
    player = world.get_players()[0]
    dimension = player.dimension
    if dimension == "nether":
        dimension = "overworld"

    print("Getting regions...")
    region_files = world.get_regions(dimension)
    print("Getting bounds...")
    xMin, xMax, zMin, zMax = 0, 0, 0, 0
    regions = []
    for region in region_files:
        parts = os.path.basename(region).split(".")
        x = int(parts[1])
        z = int(parts[2])
        regions.append((x, z))

        if x < xMin:
            xMin = x
        if x > xMax:
            xMax = x
        if z < zMin:
            zMin = z
        if z > zMax:
            zMax = z

    # region store 32x32 chunks, chunks are 16x16
    width = (xMax - xMin + 1) * 32 * 16
    height = (zMax - zMin + 1) * 32 * 16

    print("Initializing map...")
    result = Image.new("RGB", (width, height))
    data_dir = get_data_dir(world.folder)
    if not os.path.isdir(data_dir):
        os.makedirs(data_dir)

    renderable_regions = []
    for idx, region in enumerate(regions):
        print("\rChecking region %d/%d..." % (idx+1, len(regions)), end="", flush=True)
        x, z = region
        region = world.get_region(dimension, x, z)
        tile_file = os.path.join(data_dir, "%s.%s.%s.png" % (dimension, x, z))
        if os.path.isfile(tile_file) and os.path.getmtime(tile_file) > os.path.getmtime(region.filename):
            tile = Image.open(tile_file)
            result.paste(tile, ((x-xMin)*512, (z-zMin)*512))
        else:
            renderable_regions.append((x, z))
    else:
        print()

    for idx, region in enumerate(renderable_regions):
        print("\rRendering region %d/%d..." % (idx+1, len(renderable_regions)), end="", flush=True)
        x, z = region
        region = world.get_region(dimension, x, z)
        tile_file = os.path.join(data_dir, "%s.%s.%s.png" % (dimension, x, z))
        tile = render_region(region)
        tile.save(tile_file)
        result.paste(tile, ((x-xMin)*512, (z-zMin)*512))
    else:
        if len(renderable_regions):
            print()

    print("Saving world map...")
    result_filename = os.path.join(data_dir, "_%s.png" % dimension)
    result.save(result_filename, "PNG")
