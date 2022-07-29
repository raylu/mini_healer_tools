import unittest

import game_data
import wiki

class TestWiki(unittest.TestCase):
	def test_render_all_artifact_images(self):
		data = game_data.GameData()
		for key, artifact in data.artifacts.items():
			for anomaly in range(artifact.get('maxAnomaly', 0) + 1):
				with self.subTest(key, anomaly=anomaly):
					wiki.render_artifact(data, key, anomaly)

class MockRequest:
	def __init__(self, anomaly: int):
		if anomaly > 0:
			self.query = {'anomaly': anomaly}
		else:
			self.query = {}
