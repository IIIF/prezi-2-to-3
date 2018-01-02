# prezi-2-to-3

[![Build Status](https://travis-ci.org/iiif-prezi/prezi-2-to-3.svg?branch=master)](https://travis-ci.org/iiif-prezi/prezi-2-to-3)
[![Coverage Status](https://coveralls.io/repos/github/iiif-prezi/prezi-2-to-3/badge.svg?branch=master)](https://coveralls.io/github/iiif-prezi/prezi-2-to-3?branch=master)

Libraries to upgrade IIIF Presentation API manifest from v2 to v3 automatically


# Usage:

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
