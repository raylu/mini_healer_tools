import unittest

import game_data
import mini_healer_tools

class TestArtifact(unittest.TestCase):
	def test_render_all_artifacts(self):
		data = game_data.GameData()
		for key in data.artifacts.keys():
			with self.subTest(key):
				mini_healer_tools.get_artifact(None, key)
