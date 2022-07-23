import collections
import enum
import json
import re

class TalentClass(enum.IntEnum):
	DRUID = 0
	PRIEST = 1
	OCCULTIST = 2
	PALADIN = 5

class GameData:
	def __init__(self):
		self.strings = {}
		self.artifacts = {}
		self.artifact_names = collections.defaultdict(list)
		self.talents: dict = None

		for filename in ['ARTIFACT', 'ATTRIBUTE', 'CONTEXT', 'TALENT']:
			with open('extracted/' + filename, 'r', encoding='utf-8') as f:
				for line in f:
					if line in ('\n', 'END'):
						continue
					key, value = line.rstrip('\n').split('=', 1)
					assert key not in self.strings
					self.strings[key] = value

		with open('extracted/ArtifactData', 'r', encoding='utf-8') as f:
			artifact_data = json.load(f)['Artifacts']
			for artifact in artifact_data:
				try:
					name = self.resolve_string(artifact['ArtifactName'])
				except KeyError:
					continue
				self.artifacts[artifact['Key']] = artifact
				self.artifact_names[name].append(artifact['Key'])

		with open('extracted/TalentData', 'r', encoding='utf-8') as f:
			talent_data = json.load(f)['Talents']
			talent_dict = {}
			talent_strings = {}
			for talent in talent_data:
				try:
					talent['TalentName'] = self.strings[talent['TalentName']]
				except KeyError:
					continue
				key = talent['Key']
				talent['desc'] = self.strings.get('TALENT_%s_DESC' % key)
				if talent['desc'] is not None:
					talent_strings.update(self.fetch_strings(talent['desc']))
				talent_dict[key] = talent
			self.talents = {'talents': talent_dict, 'strings': talent_strings}

	def resolve_string(self, s: str) -> str:
		value = self.strings[s]
		if re.fullmatch(r'\[[A-Z_]+\]', value):
			value = self.strings[value[1:-1]]
		return value

	def fetch_strings(self, s: str) -> dict[str, str]:
		extra_strings = {}
		for m in re.finditer(r'\[(\S+)\]', s):
			var = m.group(1)
			try:
				extra_strings[var] = self.strings[var]
			except KeyError:
				pass
		return extra_strings
