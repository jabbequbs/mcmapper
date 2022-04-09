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
    if chunk["Status"].value != "full":
        return Image.frombytes("RGB", (16, 16),
            b"".join(bytes((0, 0, 0)) for _ in range(256)))
    elif isinstance(layer, int):
        heights = [layer for _ in range(256)]
    else:
        # In 1.16 and up, heightmaps are 37 longs, each with 7 values of 9 bits.  The last bit of each long
        # is unused (7*9 = 63), and the last 28 bits of the last long.
        # The heightmap for an ocean chunk looks like this:
        #   01: 0000111111000111111000111111000111111000111111000111111000111111
        #   02: 0000111111000111111000111111000111111000111111000111111000111111
        #   03: 0000111111000111111000111111000111111000111111000111111000111111
        #   ...
        #   37: 0000000000000000000000000000000111111000111111000111111000111111
        height_data = chunk["Heightmaps"][layer]
        heights = []
        for h in height_data:
            for i in range(7): # 64 // 9
                # minus one since the height will be the air block above the solid block
                heights.append((h & 0b111111111) - 1)
                h = h >> 9
                if len(heights) == 256:
                    break

    black = bytes((0, 0, 0))
    pixels = []
    sections = {}
    for z in range(16):
        for x in range(16):
            pixel_idx = z*16+x
            if heightmap:
                pixels.append(bytes((heights[pixel_idx], heights[pixel_idx], heights[pixel_idx])))
                continue
            section_y = heights[pixel_idx] // 16 + chunk["yPos"].value
            if section_y not in sections:
                if len(chunk["sections"]) == 0 or section_y == -1:
                    print('len(chunk["sections"]) == 0 or section_y == -1:')
                    pixels.append(black)
                    continue
                try:
                    section = next(section for section in chunk["sections"]
                        if section["Y"].value == section_y)
                except StopIteration:
                    try:
                        section = next(section for section in reversed(chunk["sections"])
                            if "palette" in section)
                    except StopIteration:
                        raise Exception("Weird sections (was looking for %s): %s" % (section_y, [c.tags for c in chunk["sections"]]))
                # Find the number of bits it takes to represent the largest index in the palette (at least 4)
                try:
                    index_len = max((4, len(bin(len(section["block_states"]["palette"])-1))-2))
                    index_mask = int("1"*index_len, base=2)
                except KeyError:
                    pixels.append(black)
                    continue
                # data is a list of longs, each of which has some number of indices
                # Many ocean chunks will have 16 zeros terminating the list of longs
                blocks = []
                if "data" in section["block_states"]:
                    for bs in section["block_states"]["data"]:
                        blocks.extend((bs & (index_mask << (i*index_len))) >> (i*index_len) for i in range(64//index_len))
                else:
                    blocks = [0]
                sections[section_y] = (section, blocks)

            # Get the chunk section and block states
            section, blocks = sections[section_y]
            # The block state is an index into the palette
            palette_idx = 0 if len(blocks) == 1 else blocks[(heights[pixel_idx]%16)*256+z*16+x]
            try:
                block = section["block_states"]["palette"][palette_idx]["Name"].value.replace("minecraft:", "")
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


def render_region(region, layer="WORLD_SURFACE"):
    result = Image.new("RGB", (32*16, 32*16))
    for x in range(32):
        for z in range(32):
            try:
                chunk = region.get_chunk(x, z)
            except nbt.region.InconceivedChunk:
                pass
            else:
                result.paste(render_chunk(chunk, layer), (x*16, z*16))
    return result


def render_world(world, dimension=None, force=False):
    print("Loading world...")
    if type(world) is str:
        world = LevelInfo(world)
    dimension = dimension or world.get_players()[0].dimension

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

    renderable_regions = []
    for idx, region in enumerate(regions):
        print("\rChecking region %d/%d..." % (idx+1, len(regions)), end="", flush=True)
        x, z = region
        try:
            region = world.get_region(dimension, x, z)
        except Exception as e:
            print("\n%s" % e)
            continue
        tile_file = os.path.join(data_dir, "%s.%s.%s.png" % (dimension, x, z))
        if force:
            renderable_regions.append((x, z))
        elif os.path.isfile(tile_file) and os.path.getmtime(tile_file) > os.path.getmtime(region.filename):
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
    if len(renderable_regions) > 0:
        print()

    print("Saving world map...")
    result_filename = os.path.join(data_dir, "_%s.png" % dimension)
    result.save(result_filename, "PNG")
