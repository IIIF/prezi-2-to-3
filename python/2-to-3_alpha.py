
###
### IIIF Presentation API version 2 to version 3 upgrader
###

import json
import requests

class Upgrader(object):

	def __init__(self, flags={}):
		self.crawl = flags.get("crawl", False)
		self.description_is_metadata = flags.get("desc_2_md", True)
		self.allow_extensions = flags.get("ext_ok", False)

		self.language_properties = ['label', 'attribution', 'summary']

		self.all_properties = [
			"label", "metadata", "summary", "thumbnail", "navDate",
			"attribution", "rights", "logo", "value",
			"id", "type", "format", "language", "profile", "timeMode",
			"height", "width", "duration", "viewingDirection", "behavior",
			"related", "rendering", "service", "seeAlso", "within",
			"start", "includes", "items", "structures", "annotations"]

		self.annotation_properties = ['motivation', 'stylesheet']

		self.set_properties = [
			"thumbnail", "rights", "logo", "behavior",
			"related", "rendering", "service", "seeAlso", "within"
		]

		self.object_properties = [
			"thumbnail", "logo", "related", "rendering", "service", "rights", "seeAlso", "within"]
		self.single_object_properties = ["start", "includes"]

		self.profile_map = {
			"http://library.stanford.edu/iiif/image-api/1.1/conformance.html#level0": "level0",
			"http://library.stanford.edu/iiif/image-api/1.1/conformance.html#level1": "level1",
			"http://library.stanford.edu/iiif/image-api/1.1/conformance.html#level2": "level2",
			"http://iiif.io/api/image/1/level0.json": "level0",
			"http://iiif.io/api/image/1/level1.json": "level1",
			"http://iiif.io/api/image/1/level2.json": "level2",
			"http://iiif.io/api/image/2/level0.json": "level0",
			"http://iiif.io/api/image/2/level1.json": "level1",
			"http://iiif.io/api/image/2/level2.json": "level1",	
			"http://iiif.io/api/auth/1/kiosk": "kiosk",
			"http://iiif.io/api/auth/1/login": "login",
			"http://iiif.io/api/auth/1/clickthrough": "clickthrough",
			"http://iiif.io/api/auth/1/external": "external"	
		}
		
		self.property_map = {
			'@id': 'id',
			'@type': 'type',
			'startCanvas': 'start',
			'contentLayer': 'includes',
			'license': 'rights',
			'viewingHint': 'behavior',
			'sequences': 'items',
			'resource': 'body',
			'on': 'target',
			'full': 'source',
			'style': 'styleClass'
		}

		self.id_type_cache = {}



	def retrieve_resource(self, uri):
		resp = requests.get(uri)
		return resp.json()

	def traverse(self, what):
		new = {}
		for (k,v) in what.items():
			if k in self.language_properties:
				new[k] = v
				continue
			elif k == 'metadata':
				# also handled by language_map
				new[k] = v
				continue
			if type(v) == dict:
				new[k] = self.process_resource(v)
			elif type(v) == list:
				newl = []
				for i in v:
					if type(i) == dict:
						newl.append(self.process_resource(i))
					else:
						newl.append(i)
				new[k] = newl
			else:
				new[k] = v
		return new

	def property_names(self, what):
		new = {}
		for (k,v) in self.property_map.items():
			if what.has_key(k):
				new[v] = what[k]
				del what[k]

		if what.has_key('description'):
			if self.description_is_metadata:
				# find where metadata is now
				md = what.get('metadata', [])
				if md:
					del what['metadata']
				md.append({"label": u"Description", "value": what['description']})
				new['metadata'] = md
			else:
				# rename to summary
				new['summary'] = what['description']
			del what['description']

		if 'type' in new:
			# merge members, collections, manifests on collection
			if new['type'] == 'sc:Collection':
				nl = []
				mfsts = what.get('manifests', [])		
				colls = what.get('collections', [])
				members = what.get('members', [])
				nl.extend(colls)
				nl.extend(mfsts)
				nl.extend(members)
				if nl:
					new['items'] = nl
				if mfsts:
					del what['manifests']
				if colls:
					del what['collections']
				if members:
					del what['members']

			# merge members, canvases, ranges on range
			elif new['type'] == 'sc:Range':
				nl = []
				ranges = what.get('ranges', [])		
				canvases = what.get('canvases', [])
				members = what.get('members', [])
				nl.extend(ranges)
				nl.extend(canvases)
				nl.extend(members)
				if nl:
					new['items'] = nl
				if ranges:
					del what['ranges']
				if canvases:
					del what['canvases']
				if members:
					del what['members']		

			elif new['type'] == 'oa:Annotation':
				for p in self.annotation_properties:
					if what.has_key(p):
						new[p] = what[p]
						del what[p]
			elif new['type'] == 'oa:Choice':
				newl = []
				if what.has_key('default'):
					newl.append(what['default'])
					del what['default']
				if what.has_key('item'):
					v = what['item']
					if type(v) != list:
						v = [v]
					newl.extend(v)
					del what['item']
				new['items'] = newl
			elif new['type'] == 'oa:CssStyle' or 'oa:CssStyle' in new['type']:
				new['type'] = "CssStylesheet"
				if "chars" in what:
					new['value'] = what['chars']
					del what['chars']

		if what.has_key('canvases'):
			# on a Sequence
			new['items'] = what['canvases']
			del what['canvases']

		# images -> items, with extra structure
		if what.has_key('images'):
			newl = {'type': 'AnnotationPage', 'items': []}
			for anno in what['images']:
				newl['items'].append(anno)
			new['items'] = [newl]
			del what['images']

		# otherContent goes to either annotations or items, depending
		# on motivation of the Annotation :/
		if what.has_key('otherContent'):
			# XXX urgh
			pass


		for p in self.all_properties:
			if what.has_key(p):
				new[p] = what[p]
				del what[p]

		if not self.allow_extensions and what:
			raise ValueError("unable to handle keys: %s on %s" % (what.keys(), new))

		return new

	def type_names(self, what):
		t = what.get('type', '')
		if t:
			if t.startswith('sc:'):
				t = t.replace('sc:', '')
			elif t.startswith('oa:'):
				t = t.replace('oa:', '')
			elif t.startswith('dctypes:'):
				t = t.replace('dctypes:', '')
			if t == "Layer":
				t = "AnnotationCollection"
			elif t == "AnnotationList":
				t = "AnnotationPage"
			what['type'] = t
		return what

	def motivation_names(self, what):
		m = what.get('motivation', '')
		if m:
			if m.startswith('sc:'):
				m = m.replace('sc:', '')
			elif m.startswith('oa:'):
				m = m.replace('oa:', '')
			what['motivation'] = m
		return what


	def do_language_map(self, value):
		new = {}
		if type(value) == unicode:
			new['@none'] = [value]
		elif type(value) == dict:
			try:
				new[value['@language']].append(value['@value'])
			except:
				new[value['@language']] = [value['@value']]
		elif type(value) == list:
			for i in value:
				if type(i) == unicode:
					try:
						new['@none'].append(i)
					except:
						new['@none'] = [i]
				elif type(i) == dict:
					try:
						new[i['@language']].append(i['@value'])
					except:
						new[i['@language']] = [i['@value']]
		return new


	def language_map(self, what):
		for p in self.language_properties:
			if p in what:
				try:
					what[p] = self.do_language_map(what[p])
				except:
					print what
					raise
		if 'metadata' in what:
			newmd = []
			for pair in what['metadata']:
				l = self.do_language_map(pair['label'])
				v = self.do_language_map(pair['value'])
				newmd.append({'label': l, 'value': v})
			what['metadata'] = newmd
		return what

	def container_set(self, what):
		for p in self.set_properties:
			if p in what:
				v = what[p]
				if type(v) != list:
					v = [v]
				what[p] = v
		return what

	def objects(self, what):
		for p in self.object_properties:
			if p in what:
				new = []
				for v in what[p]:
					if type(v) == dict:
						new.append(v)
					else:
						new.append({'id': v})
				what[p] = new
		for p in self.single_object_properties:
			if p in what:
				v = what[p]
				if type(v) == dict:
					what[p] = v
				else:
					if p == 'start':
						pt = "Canvas"
					elif p == 'includes':
						pt = "AnnotationCollection"
					what[p] = {'id': v, 'type': pt}

		return what

	def embedded_context(self, what):
		if "@context" in what:
			# manage known service contexts
			ctxt = what['@context']
			if ctxt == "http://iiif.io/api/image/2/context.json":
				what['type'] = "ImageService2"
			elif ctxt == "http://iiif.io/api/image/1/context.json":
				what['type'] = "ImageService2"
			elif ctxt == "http://iiif.io/api/search/1/context.json":
				what['type'] = "SearchService1"				
			else:
				print "Cannot handle context: %s" % ctxt
				raise ValueError()
			del what['@context']
		return what

	def profiles(self, what):
		if "profile" in what:
			p = what['profile']
			if p == "http://iiif.io/api/search/1/autocomplete":
				what['type'] = "AutoCompleteService1"
				del what['profile']
			elif p == "http://iiif.io/api/search/1/search":
				what['type'] = "SearchService1"
				del what['profile']
			elif p == "http://iiif.io/api/auth/1/token":
				what['type'] = "TokenService1"
				del what['profile']
			elif p in self.profile_map:
				what['profile'] = self.profile_map[p]
			else:
				print "Unrecognized profile: %s (continuing)" % p
		return what

	def ranges(self, what):
		if "structures" in what:
			rngs = what['structures']
			# unflatten, kill 'top'
			new = []
			rids = {}
			for r in rngs:

				print repr(r)
				rid = r['id']
				rids[rid] = r





		return what


	def process_resource(self, what, top=False):

		if top:
			# process @context
			orig_context = what.get("@context", "")
			# could be a list with extensions etc
			del what['@context']
		else:
			what = self.embedded_context(what)

		what = self.property_names(what)
		what = self.type_names(what)
		what = self.motivation_names(what)
		what = self.profiles(what)
		what = self.language_map(what)
		what = self.container_set(what)
		what = self.objects(what)		

		if 'id' in what:
			self.id_type_cache[what['id']] = what.get('type', '')

		what = self.traverse(what)
		what = self.ranges(what)



		if top:
			if orig_context != "http://iiif.io/api/presentation/2/context.json":
				# uhh...
				pass
			else:
				what['@context'] = [
    				"http://www.w3.org/ns/anno.jsonld",
    				"http://iiif.io/api/presentation/3/context.json"]

		return what

	def process_uri(self, uri, top=False):
		what = self.retrieve_resource(uri)
		return self.process_resource(what, top)


if __name__ == "__main__":

	upgrader = Upgrader(flags={"ext_ok": False})

	# Process all of the fixtures
	uri = "http://iiif.io/api/presentation/2.1/example/fixtures/collection.json"
	uri = "http://iiif.io/api/presentation/2.1/example/fixtures/65/manifest.json"
	uri = "http://media.nga.gov/public/manifests/nga_highlights.json"
	uri = "https://iiif.lib.harvard.edu/manifests/drs:48309543"


	results = upgrader.process_uri(uri, True)
	print json.dumps(results, indent=2, sort_keys=True)



### TO DO:

### The more complicated stuff

# Determine which annotations should be items and which annotations
# -- this is non trivial, but also not common

# Try to add type to content resources
# -- probably either text or image in 2.x, but might have to bail sometimes
# This can be hard, and impossible for the examples as they're not real

# Unflatten Ranges
# Programmatic but code is more involved than single subsitution
# Question for what to do in case of loops and graphs, if they're found

### Cardinality Requirements
# Check all presence of all MUSTs in the spec and maybe bail

# A Collection must have at least one label.
# A Manifest must have at least one label.
# An AnnotationCollection must have at least one label.
# id on Collection, Manifest, Canvas, content, Range, 
#    AnnotationCollection, AnnotationPage, Annotation
# type on all
# width+height pair for Canvas, if either
# items all the way down
