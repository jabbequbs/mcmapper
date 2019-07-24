#!/usr/bin/env python3

import argparse
import glob
import os

from mapper import render_map

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="The map file or folder")
    args = parser.parse_args()

    if os.path.isfile(args.filename):
        filenames = [args.filename]
    elif os.path.isdir(args.filename):
        pattern = os.path.join(args.filename, "map_*.dat")
        filenames = glob.glob(pattern)

    outputfilename = os.path.join("maps", "%s.png")
    for filename in filenames:
        rendered_map = render_map(filename, True)
        this_outputfilename = outputfilename % os.path.basename(filename)
        print("Saving to %s..." % this_outputfilename)
        rendered_map.save(this_outputfilename)

if __name__ == '__main__':
    main()
