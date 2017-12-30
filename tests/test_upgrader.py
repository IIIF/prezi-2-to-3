import unittest

from iiif_prezi_upgrader import prezi_upgrader

class TestUpgrader(unittest.TestCase):
	
	def setUp(self):
		flags= {"ext_ok": False, "deref_links": False}
		self.upgrader = prezi_upgrader.Upgrader(flags)
		self.results = self.upgrader.process_cached('tests/input_data/manifest-basic.json')

	def test_context(self):
		newctxt = ["http://www.w3.org/ns/anno.jsonld",
			"http://iiif.io/api/presentation/3/context.json"]
		self.assertTrue('@context' in self.results)
		self.assertEqual(self.results['@context'], newctxt)

	def test_items(self):
		self.assertTrue('items' in self.results)
		self.assertTrue('items' in self.results['items'][0])
		self.assertTrue('items' in self.results['items'][0]['items'][0])
		self.assertTrue('items' in self.results['structures'][0])
		self.assertTrue('items' in self.results['structures'][0]['items'][1])

	def test_id(self):
		self.assertTrue('id' in self.results)
		self.assertEqual(self.results['id'], \
			"http://iiif.io/api/presentation/2.1/example/fixtures/1/manifest.json")
		self.assertTrue('id' in self.results['structures'][0])
		self.assertTrue('id' in self.results['items'][0]['items'][0])

	def test_type(self):
		# Also tests values of type
		self.assertTrue('type' in self.results)
		self.assertEqual(self.results['type'], "Manifest")
		self.assertTrue('type' in self.results['items'][0])
		self.assertEqual(self.results['items'][0]['type'], 'Sequence')
		cvs = self.results['items'][0]['items'][0]
		self.assertEqual(cvs['type'], 'Canvas')
		self.assertEqual(cvs['items'][0]['type'], "AnnotationPage")
		self.assertEqual(cvs['items'][0]['items'][0]['type'], "Annotation")

	def test_startCanvas(self):
		cvs = "http://iiif.io/api/presentation/2.1/example/fixtures/canvas/1/c1.json"
		self.assertTrue('start' in self.results)
		self.assertEqual(self.results['start']['id'], cvs)
		self.assertTrue('start' in self.results['items'][0])
		self.assertEqual(self.results['items'][0]['start']['id'], cvs)
		self.assertEqual(self.results['start']['type'], 'Canvas')

	def test_license(self):
		lic = "http://iiif.io/event/conduct/"
		self.assertTrue('rights' in self.results)
		self.assertEqual(self.results['rights'][0]['id'], lic)

	def test_viewingHint(self):
		self.assertTrue('behavior' in self.results)
		self.assertEqual(self.results['behavior'], ["paged"])
		self.assertTrue('behavior' in self.results['items'][0])
		self.assertEqual(self.results['items'][0]['behavior'], ["paged"])


	def test_arrays(self):
		self.assertEqual(type(self.results['behavior']), list)
		self.assertEqual(type(self.results['logo']), list)
		self.assertEqual(type(self.results['seeAlso']), list)

	def test_uri_string(self):
		self.assertEqual(type(self.results['rendering'][0]), dict)
		self.assertEqual(type(self.results['rights'][0]), dict)
		self.assertEqual(type(self.results['start']), dict)

	def test_languagemap(self):
		self.assertEqual(type(self.results['label']), dict)
		self.assertTrue('@none' in self.results['label'])
		self.assertEqual(self.results['label']['@none'], ["Manifest Label"])
		self.assertTrue('metadata' in self.results)
		md = self.results['metadata']
		self.assertEqual(type(md[0]['label']), dict)
		self.assertEqual(type(md[0]['label']['@none']), list)
		self.assertEqual(md[0]['label']['@none'][0], "MD Label 1")
		self.assertEqual(type(md[0]['value']), dict)		
		self.assertEqual(type(md[0]['value']['@none']), list)
		self.assertEqual(md[0]['value']['@none'][0], "MD Value 1")

		# md[1] has two values 
		self.assertEqual(len(md[1]['value']['@none']), 2)
		# md[2] has en and fr values
		self.assertTrue('en' in md[2]['value'])
		self.assertTrue('fr' in md[2]['value'])

	def test_description(self):
		if self.upgrader.description_is_metadata:
			# look in metadata
			found = 0
			for md in self.results['metadata']:
				if md['label']['@none'][0] == "Description":
					found = 1
					self.assertEqual(md['value']['@none'][0], 
						"This is a description of the Manifest")					
			# ensure it was generated 
			self.assertEqual(found, 1)
		else:
			# look in summary
			self.assertTrue('summary' in self.results)
			self.assertEqual(type(self.results['summary']), dict)
			self.assertTrue('@none' in self.results['summary'])
			self.assertEqual(self.results['summary']['@none'][0], 
				"This is a description of the Manifest")
