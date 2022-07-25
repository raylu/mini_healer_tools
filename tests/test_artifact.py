import unittest

import game_data
import mini_healer_tools

class TestArtifact(unittest.TestCase):
	def test_render_all_artifacts(self):
		data = game_data.GameData()
		for key, artifact in data.artifacts.items():
			for anomaly in range(artifact.get('maxAnomaly', 0) + 1):
				with self.subTest(key, anomaly=anomaly):
					mini_healer_tools.get_artifact(MockRequest(anomaly), key)

class MockRequest:
	def __init__(self, anomaly: int):
		if anomaly > 0:
			self.query = {'anomaly': anomaly}
		else:
			self.query = {}
