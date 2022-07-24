import collections
import enum
import json
import re
import typing

class TalentClass(enum.IntEnum):
	DRUID = 0
	PRIEST = 1
	OCCULTIST = 2
	PALADIN = 5

class GameData:
	def __init__(self, artifact_descriptions=True):
		self.strings: dict[str, str] = {}
		self.artifacts: dict[str, dict] = {}
		self.artifact_names: dict[str, dict] = {}
		self.artifact_descriptions: dict[str, list[str]] = None
		self.artifact_attributes: dict[str, list[dict]] = None
		self.talents: dict = None

		for filename in ['ARTIFACT', 'ATTRIBUTE', 'CONTEXT', 'TALENT']:
			with open('extracted/' + filename, 'r', encoding='utf-8') as f:
				self.strings.update(parse_translation(f))

		artifact_name_to_keys = collections.defaultdict(list)
		with open('extracted/ArtifactData', 'r', encoding='utf-8') as f:
			artifact_data = json.load(f)['Artifacts']
			for artifact in artifact_data:
				try:
					name = self.resolve_string(artifact['ArtifactName'])
				except KeyError:
					continue
				self.artifacts[artifact['Key']] = artifact
				artifact_name_to_keys[name].append(artifact['Key'])
		for name, keys in artifact_name_to_keys.items():
			rarities = {self.artifacts[key].get('Rarity') for key in keys}
			(rarity,) = rarities
			self.artifact_names[name] = {'keys': keys, 'rarity': rarity}
		if artifact_descriptions:
			with open('extracted/artifact_descriptions.json', 'r', encoding='utf-8') as f:
				self.artifact_descriptions = json.load(f)
		with open('extracted/artifact_attributes.json', 'r', encoding='utf-8') as f:
			self.artifact_attributes = json.load(f)

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

def parse_translation(f: typing.TextIO) -> dict[str, str]:
	strings: dict[str, str] = {}
	for line in f:
		if line in ('\n', 'END'):
			continue
		key, value = line.rstrip('\n').split('=', 1)
		assert key not in strings
		strings[key] = value
	return strings
