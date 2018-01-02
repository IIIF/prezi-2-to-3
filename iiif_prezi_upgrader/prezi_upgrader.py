
###
### IIIF Presentation API version 2 to version 3 upgrader
###

import json
import requests

try:
        STR_TYPES = [str, unicode] #Py2
except:
        STR_TYPES = [bytes, str] #Py3

class Upgrader(object):

	def __init__(self, flags={}):
		self.crawl = flags.get("crawl", False)
		self.description_is_metadata = flags.get("desc_2_md", True)
		self.related_is_metadata = flags.get("related_2_md", False)
		self.allow_extensions = flags.get("ext_ok", False)
		self.default_lang = flags.get("default_lang", "@none")
		self.deref_links = flags.get("deref_links", True)
		self.debug = flags.get('debug', False)

		self.id_type_hash = {}

		self.language_properties = ['label', 'attribution', 'summary']

		self.all_properties = [
			"label", "metadata", "summary", "thumbnail", "navDate",
			"attribution", "rights", "logo", "value",
			"id", "type", "format", "language", "profile", "timeMode",
			"height", "width", "duration", "viewingDirection", "behavior",
			"related", "rendering", "service", "seeAlso", "within",
			"start", "includes", "items", "structures", "annotations"]

		self.annotation_properties = [
			"body", "target", "motivation", "source", "selector", "state", 
			"stylesheet", "styleClass"
		]

		self.set_properties = [
			"thumbnail", "rights", "logo", "behavior",
			"related", "rendering", "service", "seeAlso", "within"
		]

		self.object_property_types = {
			"thumbnail": "Image", 
			"logo":"Image", 
			"related": "", 
			"rendering": "", 
			"service": "Service", 
			"rights": "", 
			"seeAlso": "Dataset", 
			"within": ""
		}

		self.profile_map = {
			"http://library.stanford.edu/iiif/image-api/1.1/conformance.html#level0": "level0",
			"http://library.stanford.edu/iiif/image-api/1.1/conformance.html#level1": "level1",
			"http://library.stanford.edu/iiif/image-api/1.1/conformance.html#level2": "level2",
           "http://library.stanford.edu/iiif/image-api/1.1/compliance.html#level1": "level1",
           "http://library.stanford.edu/iiif/image-api/1.1/compliance.html#level2": "level2",
			"http://iiif.io/api/image/1/level0.json": "level0",
			"http://iiif.io/api/image/1/level1.json": "level1",
			"http://iiif.io/api/image/1/level2.json": "level2",
			"http://iiif.io/api/image/2/level0.json": "level0",
			"http://iiif.io/api/image/2/level1.json": "level1",
			"http://iiif.io/api/image/2/level2.json": "level1",	
			"http://iiif.io/api/auth/1/kiosk": "kiosk",
			"http://iiif.io/api/auth/1/login": "login",
			"http://iiif.io/api/auth/1/clickthrough": "clickthrough",
			"http://iiif.io/api/auth/1/external": "external",	
			"http://iiif.io/api/auth/0/kiosk": "kiosk",
			"http://iiif.io/api/auth/0/login": "login",
			"http://iiif.io/api/auth/0/clickthrough": "clickthrough",
			"http://iiif.io/api/auth/0/external": "external"
		}
		
		self.content_type_map = {
			"image": "Image",
			"audio": "Sound",
			"video": "Video",
			"application/pdf": "Text",
			"text/html": "Text",
			"text/plain": "Text",
			"application/xml": "Dataset",
			"text/xml": "Dataset"
		}

	def warn(self, msg):
		if self.debug:
			print(msg)

	def retrieve_resource(self, uri):
		resp = requests.get(uri, verify=False)
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
			elif k == 'structures':
				# processed by Manifest directly to unflatten
				new[k] = v
				continue
			if type(v) == dict:
				if not v.keys() == ['type', 'id']:
					new[k] = self.process_resource(v)
				else:
					new[k] = v
			elif type(v) == list:
				newl = []
				for i in v:
					if type(i) == dict:
						if not i.keys() == ['type', 'id']:
							newl.append(self.process_resource(i))
						else:
							newl.append(i)
					else:
						newl.append(i)
				new[k] = newl
			else:
				new[k] = v
			if not k in self.all_properties and not k in self.annotation_properties:
				self.warn("Unknown property: %s" % k)

		return new

	def fix_service_type(self, what):
		# manage known service contexts
		# assumes an answer to https://github.com/IIIF/api/issues/1352
		if '@context' in what:
			ctxt = what['@context']
			if ctxt == "http://iiif.io/api/image/2/context.json":
				what['type'] = "ImageService2"
				del what['@context']
				return what				
			elif ctxt in ["http://iiif.io/api/image/1/context.json",
				"http://library.stanford.edu/iiif/image-api/1.1/context.json"]:				
				what['type'] = "ImageService1"			
				del what['@context']
				return what
			elif ctxt in ["http://iiif.io/api/search/1/context.json",
				"http://iiif.io/api/search/0/context.json",
				"http://iiif.io/api/auth/1/context.json",
				"http://iiif.io/api/auth/0/context.json"]:
				# handle below in profiles, but delete context here
				del what['@context']
			elif ctxt == "http://iiif.io/api/annex/openannotation/context.json":
				what['type'] = "ImageApiSelector"
				del what['@context']
			else:
				self.warn("Unknown context: %s" % ctxt)

		if 'profile' in what:
			# Auth: CookieService1 , TokenService1
			profile = what['profile']
			if profile in [
				"http://iiif.io/api/auth/1/kiosk",
				"http://iiif.io/api/auth/1/login",
				"http://iiif.io/api/auth/1/clickthrough",
				"http://iiif.io/api/auth/1/external",
				"http://iiif.io/api/auth/0/kiosk",
				"http://iiif.io/api/auth/0/login",
				"http://iiif.io/api/auth/0/clickthrough",
				"http://iiif.io/api/auth/0/external"
				]:
				what['type'] = 'AuthCookieService1'
				# leave profile alone
			elif profile in ["http://iiif.io/api/auth/1/token",
				"http://iiif.io/api/auth/0/token"]:
				what['type'] = 'AuthTokenService1'
				del what['profile']
			elif profile in ["http://iiif.io/api/auth/1/logout",
				"http://iiif.io/api/auth/0/logout"]:
				what['type'] = 'AuthLogoutService1'
				del what['profile']
			elif profile in ["http://iiif.io/api/search/1/search",
				"http://iiif.io/api/search/0/search"]:
				what['type'] = "SearchService1"
				del what['profile']
			elif profile in ["http://iiif.io/api/search/1/autocomplete",
				"http://iiif.io/api/search/0/autocomplete"]:
				what['type'] = "AutoCompleteService1"
				del what['profile']
		return what

	def fix_type(self, what):
		# Called from process_resource so we can switch
		t = what.get('@type', '')
		if t:
			if type(t) == list:
				if 'oa:CssStyle' in t:
					t = "CssStylesheet"
				elif 'cnt:ContentAsText' in t:
					t = "TextualBody"
			if t.startswith('sc:'):
				t = t.replace('sc:', '')
			elif t.startswith('oa:'):
				t = t.replace('oa:', '')
			elif t.startswith('dctypes:'):
				t = t.replace('dctypes:', '')
			elif t.startswith('iiif:'):
				# e.g iiif:ImageApiSelector
				t = t.replace('iiif:', '')
			if t == "Layer":
				t = "AnnotationCollection"
			elif t == "AnnotationList":
				t = "AnnotationPage"
			elif t == "cnt:ContentAsText":
				t = "TextualBody"
			what['type'] = t
			del what['@type']
		else:
			# Upgrade service types based on contexts & profiles
			what = self.fix_service_type(what)
		return what

	def do_language_map(self, value):
		new = {}
		defl = self.default_lang
		if type(value) in STR_TYPES:
			new[defl] = [value]
		elif type(value) == dict:
			try:
				new[value['@language']].append(value['@value'])
			except:
				new[value['@language']] = [value['@value']]
		elif type(value) == list:
			for i in value:
				if type(i) == dict:
					try:
						new[i['@language']].append(i['@value'])
					except:
						new[i['@language']] = [i['@value']]
				elif type(i) == list:
					pass
				elif type(i) == dict:
					# UCD has just {"@value": ""}
					if not '@language' in i:
						i['@language'] = '@none'
					try:
						new[i['@language']].append(i['@value'])
					except:
						new[i['@language']] = [i['@value']]
				else:  # string value
					try:
						new[defl].append(i)
					except:
						new[defl] = [i]

		else:  # string value
			new[defl] = [value]
		return new

	def fix_languages(self, what):
		for p in self.language_properties:
			if p in what:
				try:
					what[p] = self.do_language_map(what[p])
				except:
					raise
		if 'metadata' in what:
			newmd = []
			for pair in what['metadata']:
				l = self.do_language_map(pair['label'])
				v = self.do_language_map(pair['value'])
				newmd.append({'label': l, 'value': v})
			what['metadata'] = newmd
		return what

	def fix_sets(self, what):
		for p in self.set_properties:
			if p in what:
				v = what[p]
				if type(v) != list:
					v = [v]
				what[p] = v
		return what

	def fix_objects(self, what):
		for (p,typ) in self.object_property_types.items():
			if p in what:
				new = []
				for v in what[p]:
					if not type(v) == dict:
						v = {'id':v}
					if not 'type' in v and typ:
						v['type'] = typ
					elif not 'type' in v and 'id' in v and v['id'] in self.id_type_hash:
						v['type'] = self.id_type_hash[v['id']]
					elif self.deref_links:
						# do a HEAD on the resource and look at Content-Type
						try:
							h = requests.head(v['id'])
						except:
							# dummy URI
							h = None
						if h and h.status_code == 200:
							ct = h.headers['content-type']
							v['format'] = ct  # as we have it...
							ct = ct.lower()
							first = ct.split('/')[0]

							if first in self.content_type_map:
								v['type'] = self.content_type_map[first]
							elif ct in self.content_type_map:
								v['type'] = self.content_type_map[ct]
							elif ct.startswith("application/json") or \
								ct.startswith("application/ld+json"):
								# Try and fetch and look for a type!
								fh = requests.get(v['id'])
								data = fh.json()
								if 'type' in data:
									v['type'] = data['type']
								elif '@type' in data:
									data = self.fix_type(data)
									v['type'] = data['type']

					if not 'type' in v:
						self.warn("Don't know type for %s: %s" % (p, what[p]))
					new.append(v)
				what[p] = new
		return what

	def process_generic(self, what):
		if '@id' in what:
			what['id'] = what['@id']
			del what['@id']
		# @type already processed
		# Now add to id/type hash for lookups
		if 'id' in what and 'type' in what:
			self.id_type_hash[what['id']] = what['type']

		if 'license' in what:
			what['rights'] = what['license']
			del what['license']
		if 'viewingHint' in what:
			what['behavior'] = what['viewingHint']
			del what['viewingHint']
		if 'description' in what:
			if self.description_is_metadata:
				# Put it in metadata
				md = what.get('metadata', [])
				# NB this must happen before fix_languages
				md.append({"label": u"Description", "value": what['description']})
				what['metadata'] = md
			else:
				# rename to summary
				what['summary'] = what['description']
			del what['description']
		if 'related' in what:
			if self.related_is_metadata:
				md = what.get('metadata', [])
				# NB this must happen before fix_languages
				md.append({"label": u"Related", "value": "<a href='%s'>Related Document</a>" % what['related']})
				what['metadata'] = md
			else:
				what['homepage'] = {"id": what['related'], "type": "Text"}
			del what['related']

		if "profile" in what:
			p = what['profile']
			if type(p) == list and p[0].startswith('http://iiif.io/api/image/'):
				# URGH embedded Image API info.
				# Leave it alone, I think
				pass
			elif p in self.profile_map:
				what['profile'] = self.profile_map[p]
			else:
				self.warn("Unrecognized profile: %s (continuing)" % p)

		if "otherContent" in what:
			# otherContent is already AnnotationList, so no need to inject
			what['annotations'] = what['otherContent']
			del what['otherContent']

		what = self.fix_languages(what)
		what = self.fix_sets(what)
		what = self.fix_objects(what)

		return what

	def process_collection(self, what):
		what = self.process_generic(what)

		if 'members' in what:
			what['items'] = what['members']
			del what['members']
		else:
			nl = []
			colls = what.get('collections', [])
			for c in colls:
				if not type(c) == dict:
					c = {'id': c, 'type': 'Collection'}
				elif not 'type' in c:
					c['type'] = 'Collection'
				nl.append(c)
			mfsts = what.get('manifests', [])		
			for m in mfsts:
				if not type(m) == dict:
					m = {'id': m, 'type': 'Manifest'}
				elif not 'type' in m:
					m['type'] = 'Manifest'
				nl.append(m)			
			if nl:
				what['items'] = nl
		if 'manifests' in what:
			del what['manifests']
		if 'collections' in what:
			del what['collections']
		return what

	def process_manifest(self, what):
		what = self.process_generic(what)

		if 'startCanvas' in what:
			v = what['startCanvas']
			if type(v) != dict:
				what['start'] = {'id': v, 'type': "Canvas"}
			else:
				v['type'] = "Canvas"
				what['start'] = v
			del what['startCanvas']

		# Need to test as might not be top object
		if 'sequences' in what:
			what['items'] = what['sequences']
			del what['sequences']

		return what

	def process_range(self, what):
		what = self.process_generic(what)

		members = what.get('members', [])
		if 'members' in what:
			its = what['members']
			del what['members']
			nl = []
			for i in its:
				if not type(i) == dict:
					# look in id/type hash
					if i in self.id_type_hash:
						nl.append({"id": i, "type": self.id_type_hash[i]})
					else:
						nl.append({"id": i})
				else:
					nl.append(i)
			what['items'] = nl
		else:
			nl = []
			rngs = what.get('ranges', [])
			for r in rngs:
				if not type(r) == dict:
					r = {'id': r, 'type': 'Range'}
				elif not 'type' in r:
					r['type'] = 'Range'
				nl.append(r)
			cvs = what.get('canvases', [])		
			for c in cvs:
				if not type(c) == dict:
					c = {'id': c, 'type': 'Canvas'}
				elif not 'type' in c:
					c['type'] = 'Canvas'
				nl.append(c)			
			what['items'] = nl

		if 'canvases' in what:
			del what['canvases']
		if 'ranges' in what:
			del what['ranges']

		# contentLayer
		if 'contentLayer' in what:
			v = what['contentLayer']
			if type(v) == list and len(v) == 1:
				v = v[0]
			if type(v) != dict:
				what['includes'] = {'id': v, 'type': "AnnotationCollection"}
			else:
				v['type'] = "AnnotationCollection"
				what['includes'] = v
			del what['contentLayer']

		# Remove redundant 'top' Range
		if 'behavior' in what and 'top' in what['behavior']:
			what['behavior'].remove('top')
			# if we're empty, remove it
			if not what['behavior']:
				del what['behavior']

		if 'includes' in what:
			# single object
			what['includes'] = self.process_resource(what['includes'])

		return what

	def process_sequence(self, what):
		what = self.process_generic(what)
		what['items'] = what['canvases']
		del what['canvases']

		if 'startCanvas' in what:
			v = what['startCanvas']
			if type(v) != dict:
				what['start'] = {'id': v, 'type': "Canvas"}
			else:
				v['type'] = "Canvas"
				what['start'] = v
			del what['startCanvas']

		return what

	def process_canvas(self, what):

		# XXX process otherContent here before generic grabs it

		what = self.process_generic(what)

		if 'images' in what:
			newl = {'type': 'AnnotationPage', 'items': []}
			for anno in what['images']:
				newl['items'].append(anno)
			what['items'] = [newl]
			del what['images']
		return what

	def process_layer(self, what):
		what = self.process_generic(what)
		return what

	def process_annotationpage(self, what):
		what = self.process_generic(what)

		# XXX label is affected by undecided IIIF/api#1195

		if 'resources' in what:
			what['items'] = what['resources']
			del what['resources']
		elif not 'items' in what:
			what['items'] = []

		return what

	def process_annotationcollection(self, what):
		what = self.process_generic(what)
		return what

	def process_annotation(self, what):
		what = self.process_generic(what)

		if 'on' in what:
			what['target'] = what['on']
			del what['on']
		if 'resource' in what:
			what['body'] = what['resource']
			del what['resource']

		m = what.get('motivation', '')
		if m:
			if m.startswith('sc:'):
				m = m.replace('sc:', '')
			elif m.startswith('oa:'):
				m = m.replace('oa:', '')
			what['motivation'] = m

		if 'stylesheet' in what:
			ss = what['stylesheet']
			if type(ss) == dict:
				ss['@type'] = 'oa:CssStylesheet'
				if 'chars' in ss:
					ss['value'] = ss['chars']
					del ss['chars']
			else:
				# Just a link
				what['stylesheet'] = {'@id': ss, '@type': 'oa:CssStylesheet'}
		return what

	def process_specificresource(self, what):
		what = self.process_generic(what)
		if 'full' in what:
			# And if not, it's broken...
			what['source'] = what['full']
			del what['full']
		if 'style' in what:
			what['styleClass'] = what['style']
			del what['style']
		return what

	def process_textualbody(self, what):
		if 'chars' in what:
			what['value'] = what['chars']
			del what['chars']
		return what	

	def process_choice(self, what):
		what = self.process_generic(what)

		newl = []
		if 'default' in what:
			newl.append(what['default'])
			del what['default']
		if 'item' in what:
			v = what['item']
			if type(v) != list:
				v = [v]
			newl.extend(v)
			del what['item']
		what['items'] = newl
		return what

	def post_process_generic(self, what):
		return what

	def post_process_manifest(self, what):
		# do ranges at this point, after everything else is traversed

		if 'structures' in what:
			# Need to process from here, to have access to all info
			# needed to unflatten them
			rhash = {}
			tops = []
			for r in what['structures']:
				new = self.fix_type(r)
				new = self.process_range(new)				
				rhash[new['id']] = new
				tops.append(new['id'])

			for rng in what['structures']:
				# first try to include our Range items
				newits = []
				for child in rng['items']:
					if "@id" in child:
						c = self.fix_type(child)
						c = self.process_generic(c)
					else:
						c = child

					if c['type'] == "Range" and c['id'] in rhash:
						newits.append(rhash[c['id']])
						del rhash[c['id']]
					else:
						newits.append(c)
				rng['items'] = newits

				# Harvard has a strange within based pattern
				if 'within' in rng:
					tops.remove(rng['id'])
					parid = rng['within'][0]['id']
					del rng['within']
					parent = rhash.get(parid, None)
					if not parent:
						# Just drop it on the floor?
						self.warn("Unknown parent range: %s" % parid)
					else:
						# e.g. Harvard has massive duplication of canvases
						# not wrong, but don't need it any more
						for child in rng['items']:
							for sibling in parent['items']:
								if child['id'] == sibling['id']:
									parent['items'].remove(sibling)
									break
						parent['items'].append(rng)


			what['structures'] = []
			for t in tops:
				if t in rhash:
					what['structures'].append(rhash[t])
		return what

	def process_resource(self, what, top=False):

		if top:
			# process @context
			orig_context = what.get("@context", "")
			# could be a list with extensions etc
			del what['@context']

		# First update types, so we can switch on it
		what = self.fix_type(what)
		typ = what.get('type', '')
	
		fn = getattr(self, 'process_%s' % typ.lower(), self.process_generic)

		what = fn(what)
		what = self.traverse(what)

		fn2 = getattr(self, 'post_process_%s' % typ.lower(), self.post_process_generic)
		what = fn2(what)

		if top:
			# Add back in the v3 context
			if orig_context != "http://iiif.io/api/presentation/2/context.json":
				# XXX process extensions
				pass
			else:
				what['@context'] = [
    				"http://www.w3.org/ns/anno.jsonld",
    				"http://iiif.io/api/presentation/3/context.json"]

		return what

	def process_uri(self, uri, top=False):
		what = self.retrieve_resource(uri)
		return self.process_resource(what, top)

	def process_cached(self, fn, top=True):
		with open(fn, 'r') as fh:
			data = fh.read()
		what = json.loads(data)
		return self.process_resource(what, top)


if __name__ == "__main__":

	upgrader = Upgrader(flags={"ext_ok": False, "deref_links": False})
	results = upgrader.process_cached('tests/input_data/manifest-services.json')

	#uri = "http://iiif.io/api/presentation/2.1/example/fixtures/collection.json"
	#uri = "http://iiif.io/api/presentation/2.1/example/fixtures/1/manifest.json"
	#uri = "http://iiif.io/api/presentation/2.0/example/fixtures/list/65/list1.json"
	#uri = "http://media.nga.gov/public/manifests/nga_highlights.json"
	#uri = "https://iiif.lib.harvard.edu/manifests/drs:48309543"
	#uri = "http://adore.ugent.be/IIIF/manifests/archive.ugent.be%3A4B39C8CA-6FF9-11E1-8C42-C8A93B7C8C91"
	#uri = "http://bluemountain.princeton.edu/exist/restxq/iiif/bmtnaae_1918-12_01/manifest"
	#uri = "https://api.bl.uk/metadata/iiif/ark:/81055/vdc_00000004216E/manifest.json"
	#uri = "https://damsssl.llgc.org.uk/iiif/2.0/4389767/manifest.json"
	#uri = "http://iiif.bodleian.ox.ac.uk/iiif/manifest/60834383-7146-41ab-bfe1-48ee97bc04be.json"
	#uri = "https://lbiiif.riksarkivet.se/arkis!R0000004/manifest"
	#uri = "https://d.lib.ncsu.edu/collections/catalog/nubian-message-1992-11-30/manifest.json"
	#uri = "https://ocr.lib.ncsu.edu/ocr/nu/nubian-message-1992-11-30_0010/nubian-message-1992-11-30_0010-annotation-list-paragraph.json"
	#uri = "http://iiif.harvardartmuseums.org/manifests/object/299843"
	#uri = "https://purl.stanford.edu/qm670kv1873/iiif/manifest.json"
	#uri = "http://dams.llgc.org.uk/iiif/newspaper/issue/3320640/manifest.json"
	#uri = "http://dams.llgc.org.uk/iiif/newspaper/issue/3320640/manifest.json"
	#uri = "http://manifests.ydc2.yale.edu/manifest/Admont43"
	#uri = "https://manifests.britishart.yale.edu/manifest/1474"
	#uri = "http://demos.biblissima-condorcet.fr/iiif/metadata/BVMM/chateauroux/manifest.json"
	#uri = "http://www.e-codices.unifr.ch/metadata/iiif/sl-0002/manifest.json"
	#uri = "https://data.ucd.ie/api/img/manifests/ucdlib:33064"
	#uri = "http://dzkimgs.l.u-tokyo.ac.jp/iiif/zuzoubu/12b02/manifest.json"
	#uri = "https://dzkimgs.l.u-tokyo.ac.jp/iiif/zuzoubu/12b02/list/p0001-0025.json"
	#uri = "http://www2.dhii.jp/nijl/NIJL0018/099-0014/manifest_tags.json"
	#uri = "https://data.getty.edu/museum/api/iiif/298147/manifest.json"	
	#results = upgrader.process_uri(uri, True)

	print(json.dumps(results, indent=2, sort_keys=True))



### TO DO:

# Determine which annotations should be items and which annotations
# -- this is non trivial, but also not common

### Cardinality Requirements
# Check all presence of all MUSTs in the spec and maybe bail?

# A Collection must have at least one label.
# A Manifest must have at least one label.
# An AnnotationCollection must have at least one label.
# id on Collection, Manifest, Canvas, content, Range, 
#    AnnotationCollection, AnnotationPage, Annotation
# type on all
# width+height pair for Canvas, if either
# items all the way down
