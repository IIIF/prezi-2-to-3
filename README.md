# prezi-2-to-3

[![Build Status](https://travis-ci.org/iiif/prezi-2-to-3.svg?branch=master)](https://travis-ci.org/iiif/prezi-2-to-3)
[![Coverage Status](https://coveralls.io/repos/github/iiif/prezi-2-to-3/badge.svg?branch=master)](https://coveralls.io/github/iiif/prezi-2-to-3?branch=master)

Libraries to upgrade IIIF Presentation API manifest from v2 to v3 automatically


# Usage:

There are three options on how to use this program either through Docker, installed locally or programatically. Details below:

## Using Docker

Build the docker image:

```
docker build -t prezi-2-to-3 .
```

Run the image:

```
docker run -it --rm -p 8000:80 --name upgrader prezi-2-to-3:latest
```

or run both with the following command:

```
docker build -t prezi-2-to-3 . && docker run -it --rm -p 8000:80 --name upgrader prezi-2-to-3:latest
```

Then navigating to the following page: <http://localhost:8000/index.html>.

## Installing locally

```
sudo python  setup.py install
```

You can then either run a web version or run it from the command line.

### Command line

Usage:

```
python prezi2to3.py
Usage:
	python prezi2to3.py [file_path or url to manifest] [optional output file name]
```

Examples:

```
# Convert manifest from filesystem and print results to screen
python prezi2to3.py tests/input_data/manifest-services.json

# Convert remote manfiest and save results to /tmp/upgraded.json
python prezi2to3.py http://iiif.io/api/presentation/2.1/example/fixtures/1/manifest.json /tmp/upgraded.json
```

### Web version
To run the web version:

```
 ./conversionservice.py --port 8000
```

and navigate to <http://localhost:8000/index.html>. Note the default port if not specified is 8080.

## Using programatically

Create an Upgrader, and then call `process_cached` with the path to a version 2.x IIIF Presentation API resource on disk, or `process_uri` with a URI to the same. If the JSON is already in memory, then call `process_resource` instead. The results of the call will be the JSON of the equivalent version 3.0 resource.

```python
from iiif_prezi_upgrader import Upgrader
upgrader = Upgrader(flags={"flag_name" : "flag_value"})  # create an upgrader
v3 = upgrader.process_cached("/path/to/iiif/v2/file.json")
v3 = upgrader.process_uri("http://example.org/iiif/v2/file.json")
v3 = upgrader.process_resource(json, top=True)
```

## Flags

* `desc_2_md` : The `description` property is not a summary, and hence should be put in as a `metadata` pair.  The label generated will be "Description".  The default is `True`.
* `related_2_md` : The `related` property is not a homepage, and hence should be put in as a `metadata` pair.  The label generated will be "Related". The default is `False` (and hence the property will simply be renamed as `homepage`)
* `ext_ok` : Should extensions be copied through to the new version.  The default is `False`.
* `default_lang` : The default language to use for language maps.  The default is "@none".
* `deref_links` : Should links without a `format` property be dereferenced and the HTTP response inspected for the media type?  The default is `True`.
* `debug` : Are we in debug mode and should spit out more warnings than normal? The default is `False`


# FAQ

* Does this rely on iiif-prezi's ManifestFactory? No. It has as few dependencies as possible to allow it to be ported to other languages.
* Is it up to date? It is developed by two of the IIIF Editors (@azaroth42 and @zimeon) and we try to keep it up to date with the latest draft version 3.0 Presentation API specs.
* Are PRs welcome? Yes :)
