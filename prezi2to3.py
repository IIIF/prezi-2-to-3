#!/usr/bin/env python
# encoding: utf-8
"""IIIF Convertor Service"""

import json
import os
import sys

from iiif_prezi_upgrader import Upgrader

if __name__ == "__main__":
    if len(sys.argv) != 2 and len(sys.argv) != 3:
        print ('Usage:\n\tpython prezi2to3.py [file_path or url to manifest] [optional output file name]')
        sys.exit(0)

    manifest = sys.argv[1]
    # default flags currently but if flags are assessible then could convert them to use --ext_ok=true using ArgumentParser
    upgrader = Upgrader(flags={"ext_ok": False, "deref_links": False})  # create an upgrader
    if 'http' in manifest: # should catch https as well
        v3 = upgrader.process_uri(manifest)
    else:
        v3 = upgrader.process_cached(manifest)

    if len(sys.argv) == 3:
        # output to filename
        with open(sys.argv[2], 'w') as outfile:
            json.dump(v3, outfile, indent=2)
    else:
        print(json.dumps(v3, indent=2))
