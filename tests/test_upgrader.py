import unittest

from iiif_prezi_upgrader import prezi_upgrader

class TestUpgrader(unittest.TestCase):
	
	def setUp(self):
		flags= {"ext_ok": False, "deref_links": False}
		self.upgrader = prezi_upgrader.Upgrader(flags)
		self.results = self.upgrader.process_cached('tests/input_data/manifest-basic.json')

	def test_id(self):
		self.assertTrue('id' in self.results)
		self.assertEqual(self.results['id'], \
			"http://iiif.io/api/presentation/2.1/example/fixtures/1/manifest.json")
		self.assertTrue('id' in self.results['structures'][0])
		self.assertTrue('id' in self.results['items'][0]['items'][0])