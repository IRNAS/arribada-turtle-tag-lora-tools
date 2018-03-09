import argparse
import logging
from arribada_tools import log

parser = argparse.ArgumentParser()
parser.add_argument('--debug', action='store_true', required=False)
parser.add_argument('--file', type=argparse.FileType('r'), required=True)
parser.add_argument('--format', required=False)

args = parser.parse_args()

if args.debug:
    logging.basicConfig(format='%(asctime)s\t%(module)s\t%(levelname)s\t%(message)s', level=logging.DEBUG)

data = args.file.read()
objects = log.decode_all(data)

for i in objects:
    if i.name == 'LogStart' or i.name == 'LogEnd':
        pass
    else:
        d = {}
        d[i.name] = {}
        for j in i.fields:
            d[i.name][j] = getattr(i, j)
        print d
