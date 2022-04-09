#! python3

"""
1. `python -m cProfile -o mapper.stats scripts/viewer.py WORLD --render`
2. This script to get a human readable view of the stats
"""

import argparse
import pstats
from pstats import SortKey

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("filename")
    args = parser.parse_args()

    p = pstats.Stats(args.filename)
    p.strip_dirs().sort_stats(SortKey.CUMULATIVE).print_stats()

if __name__ == '__main__':
    main()
