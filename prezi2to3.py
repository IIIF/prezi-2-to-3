#!/usr/bin/env python
# encoding: utf-8
"""IIIF Convertor Service"""

import argparse
import json
import os
import sys

from iiif_prezi_upgrader import Upgrader
from iiif_prezi_upgrader.prezi_upgrader import FLAGS

if __name__ == "__main__":
    #if len(sys.argv) != 2 and len(sys.argv) != 3:
    #    print ('Usage:\n\tpython prezi2to3.py [file_path or url to manifest] [optional output file name]')
    #    sys.exit(0)

    parser = argparse.ArgumentParser(description=__doc__.strip(),
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('manifest', metavar='manifest', type=str, help='file_path or url to manifest')
    parser.add_argument('--output', metavar='filename', type=str, help='output file name')
    for key in FLAGS:
        name=key
        description=FLAGS[key]['description']
        default=FLAGS[key]['default']
        type=type(default)
        if default == True or default == False:
            type=bool
        parser.add_argument('--%s' % name, default=default, type=type, help=description)


    args = parser.parse_args()

    manifest = args.manifest
    # default flags currently but if flags are assessible then could convert them to use --ext_ok=true using ArgumentParser
    upgrader = Upgrader(flags=vars(args))  # create an upgrader
    if 'http' in manifest: # should catch https as well
        v3 = upgrader.process_uri(manifest)
    else:
        v3 = upgrader.process_cached(manifest)

    if args.output:
        # output to filename
        with open(args.output, 'w') as outfile:
            json.dump(v3, outfile, indent=2)
    else:
        print(json.dumps(v3, indent=2))
