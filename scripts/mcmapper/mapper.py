import nbt
import os

from .data import map_colors, block_colors
from .filesystem import get_data_dir
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
    print("Loading word...")
    if type(world) is str:
        world = nbt.world.WorldFolder(world)

    print("Getting regions...")
    region_files = world.get_filenames()
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
    data_dir = get_data_dir(world)
    if not os.path.isdir(data_dir):
        os.makedirs(data_dir)

    renderable_regions = []
    for idx, region in enumerate(regions):
        print("\rChecking region %d/%d..." % (idx+1, len(regions)), end="", flush=True)
        x, z = region
        region = world.get_region(x, z)
        tile_file = os.path.join(data_dir, "%s.%s.png" % (x, z))
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
        region = world.get_region(x, z)
        tile_file = os.path.join(data_dir, "%s.%s.png" % (x, z))
        tile = render_region(region)
        tile.save(tile_file)
        result.paste(tile, ((x-xMin)*512, (z-zMin)*512))
    else:
        if len(renderable_regions):
            print()

    return result
