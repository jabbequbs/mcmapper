
import nbt

from PIL import Image


map_colors = {}

map_colors[0] = {
    0:      bytes((0, 0, 0)),
    1:      bytes((0, 0, 0)),
    2:      bytes((0, 0, 0)),
    3:      bytes((0, 0, 0)),
    4:      bytes((89, 125, 39)),
    5:      bytes((109, 153, 48)),
    6:      bytes((127, 178, 56)),
    7:      bytes((67, 94, 29)),
    8:      bytes((174, 164, 115)),
    9:      bytes((213, 201, 140)),
    10:     bytes((247, 233, 163)),
    11:     bytes((130, 123, 86)),
    12:     bytes((140, 140, 140)),
    13:     bytes((171, 171, 171)),
    14:     bytes((199, 199, 199)),
    15:     bytes((105, 105, 105)),
    16:     bytes((180, 0, 0)),
    17:     bytes((220, 0, 0)),
    18:     bytes((255, 0, 0)),
    19:     bytes((135, 0, 0)),
    20:     bytes((112, 112, 180)),
    21:     bytes((138, 138, 220)),
    22:     bytes((160, 160, 255)),
    23:     bytes((84, 84, 135)),
    24:     bytes((117, 117, 117)),
    25:     bytes((144, 144, 144)),
    26:     bytes((167, 167, 167)),
    27:     bytes((88, 88, 88)),
    28:     bytes((0, 87, 0)),
    29:     bytes((0, 106, 0)),
    30:     bytes((0, 124, 0)),
    31:     bytes((0, 65, 0)),
    32:     bytes((180, 180, 180)),
    33:     bytes((220, 220, 220)),
    34:     bytes((255, 255, 255)),
    35:     bytes((135, 135, 135)),
    36:     bytes((115, 118, 129)),
    37:     bytes((141, 144, 158)),
    38:     bytes((164, 168, 184)),
    39:     bytes((86, 88, 97)),
    40:     bytes((106, 76, 54)),
    41:     bytes((130, 94, 66)),
    42:     bytes((151, 109, 77)),
    43:     bytes((79, 57, 40)),
    44:     bytes((79, 79, 79)),
    45:     bytes((96, 96, 96)),
    46:     bytes((112, 112, 112)),
    47:     bytes((59, 59, 59)),
    48:     bytes((45, 45, 180)),
    49:     bytes((55, 55, 220)),
    50:     bytes((64, 64, 255)),
    51:     bytes((33, 33, 135)),
    52:     bytes((100, 84, 50)),
    53:     bytes((123, 102, 62)),
    54:     bytes((143, 119, 72)),
    55:     bytes((75, 63, 38)),
    56:     bytes((180, 177, 172)),
    57:     bytes((220, 217, 211)),
    58:     bytes((255, 252, 245)),
    59:     bytes((135, 133, 129)),
    60:     bytes((152, 89, 36)),
    61:     bytes((186, 109, 44)),
    62:     bytes((216, 127, 51)),
    63:     bytes((114, 67, 27)),
    64:     bytes((125, 53, 152)),
    65:     bytes((153, 65, 186)),
    66:     bytes((178, 76, 216)),
    67:     bytes((94, 40, 114)),
    68:     bytes((72, 108, 152)),
    69:     bytes((88, 132, 186)),
    70:     bytes((102, 153, 216)),
    71:     bytes((54, 81, 114)),
    72:     bytes((161, 161, 36)),
    73:     bytes((197, 197, 44)),
    74:     bytes((229, 229, 51)),
    75:     bytes((121, 121, 27)),
    76:     bytes((89, 144, 17)),
    77:     bytes((109, 176, 21)),
    78:     bytes((127, 204, 25)),
    79:     bytes((67, 108, 13)),
    80:     bytes((170, 89, 116)),
    81:     bytes((208, 109, 142)),
    82:     bytes((242, 127, 165)),
    83:     bytes((128, 67, 87)),
    84:     bytes((53, 53, 53)),
    85:     bytes((65, 65, 65)),
    86:     bytes((76, 76, 76)),
    87:     bytes((40, 40, 40)),
    88:     bytes((108, 108, 108)),
    89:     bytes((132, 132, 132)),
    90:     bytes((153, 153, 153)),
    91:     bytes((81, 81, 81)),
    92:     bytes((53, 89, 108)),
    93:     bytes((65, 109, 132)),
    94:     bytes((76, 127, 153)),
    95:     bytes((40, 67, 81)),
    96:     bytes((89, 44, 125)),
    97:     bytes((109, 54, 153)),
    98:     bytes((127, 63, 178)),
    99:     bytes((67, 33, 94)),
    100:    bytes((36, 53, 125)),
    101:    bytes((44, 65, 153)),
    102:    bytes((51, 76, 178)),
    103:    bytes((27, 40, 94)),
    104:    bytes((72, 53, 36)),
    105:    bytes((88, 65, 44)),
    106:    bytes((102, 76, 51)),
    107:    bytes((54, 40, 27)),
    108:    bytes((72, 89, 36)),
    109:    bytes((88, 109, 44)),
    110:    bytes((102, 127, 51)),
    111:    bytes((54, 67, 27)),
    112:    bytes((108, 36, 36)),
    113:    bytes((132, 44, 44)),
    114:    bytes((153, 51, 51)),
    115:    bytes((81, 27, 27)),
    116:    bytes((17, 17, 17)),
    117:    bytes((21, 21, 21)),
    118:    bytes((25, 25, 25)),
    119:    bytes((13, 13, 13)),
    120:    bytes((176, 168, 54)),
    121:    bytes((215, 205, 66)),
    122:    bytes((250, 238, 77)),
    123:    bytes((132, 126, 40)),
    124:    bytes((64, 154, 150)),
    125:    bytes((79, 188, 183)),
    126:    bytes((92, 219, 213)),
    127:    bytes((48, 115, 112)),
    128:    bytes((52, 90, 180)),
    129:    bytes((63, 110, 220)),
    130:    bytes((74, 128, 255)),
    131:    bytes((39, 67, 135)),
    132:    bytes((0, 153, 40)),
    133:    bytes((0, 187, 50)),
    134:    bytes((0, 217, 58)),
    135:    bytes((0, 114, 30)),
    136:    bytes((91, 60, 34)),
    137:    bytes((111, 74, 42)),
    138:    bytes((129, 86, 49)),
    139:    bytes((68, 45, 25)),
    140:    bytes((79, 1, 0)),
    141:    bytes((96, 1, 0)),
    142:    bytes((112, 2, 0)),
    143:    bytes((59, 1, 0)),
    144:    bytes((147, 124, 113)),
    145:    bytes((180, 152, 138)),
    146:    bytes((209, 177, 161)),
    147:    bytes((110, 93, 85)),
    148:    bytes((112, 57, 25)),
    149:    bytes((137, 70, 31)),
    150:    bytes((159, 82, 36)),
    151:    bytes((84, 43, 19)),
    152:    bytes((105, 61, 76)),
    153:    bytes((128, 75, 93)),
    154:    bytes((149, 87, 108)),
    155:    bytes((78, 46, 57)),
    156:    bytes((79, 76, 97)),
    157:    bytes((96, 93, 119)),
    158:    bytes((112, 108, 138)),
    159:    bytes((59, 57, 73)),
    160:    bytes((131, 93, 25)),
    161:    bytes((160, 114, 31)),
    162:    bytes((186, 133, 36)),
    163:    bytes((98, 70, 19)),
    164:    bytes((72, 82, 37)),
    165:    bytes((88, 100, 45)),
    166:    bytes((103, 117, 53)),
    167:    bytes((54, 61, 28)),
    168:    bytes((112, 54, 55)),
    169:    bytes((138, 66, 67)),
    170:    bytes((160, 77, 78)),
    171:    bytes((84, 40, 41)),
    172:    bytes((40, 28, 24)),
    173:    bytes((49, 35, 30)),
    174:    bytes((57, 41, 35)),
    175:    bytes((30, 21, 18)),
    176:    bytes((95, 75, 69)),
    177:    bytes((116, 92, 84)),
    178:    bytes((135, 107, 98)),
    179:    bytes((71, 56, 51)),
    180:    bytes((61, 64, 64)),
    181:    bytes((75, 79, 79)),
    182:    bytes((87, 92, 92)),
    183:    bytes((46, 48, 48)),
    184:    bytes((86, 51, 62)),
    185:    bytes((105, 62, 75)),
    186:    bytes((122, 73, 88)),
    187:    bytes((64, 38, 46)),
    188:    bytes((53, 43, 64)),
    189:    bytes((65, 53, 79)),
    190:    bytes((76, 62, 92)),
    191:    bytes((40, 32, 48)),
    192:    bytes((53, 35, 24)),
    193:    bytes((65, 43, 30)),
    194:    bytes((76, 50, 35)),
    195:    bytes((40, 26, 18)),
    196:    bytes((53, 57, 29)),
    197:    bytes((65, 70, 36)),
    198:    bytes((76, 82, 42)),
    199:    bytes((40, 43, 22)),
    200:    bytes((100, 42, 32)),
    201:    bytes((122, 51, 39)),
    202:    bytes((142, 60, 46)),
    203:    bytes((75, 31, 24)),
    204:    bytes((26, 15, 11)),
    205:    bytes((31, 18, 13)),
    206:    bytes((37, 22, 16)),
    207:    bytes((19, 11, 8)),
}

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
