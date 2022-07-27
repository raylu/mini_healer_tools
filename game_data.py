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

class DamageElement(enum.IntEnum):
	# see DamageData.cs
	PHYSICAL = 0
	FIRE = 1
	ICE = 2
	LIGHTNING = 3
	NEMESIS = 4

class Difficulty(enum.IntEnum):
	# see Level.cs
	NORMAL = 0
	BRUTAL = 1
	INSANE = 2

TRANSLATION_FILES = ['ARTIFACT', 'ATTRIBUTE', 'BOSS', 'CONTEXT', 'EFFECT', 'MATERIAL', 'SKILL', 'TALENT', 'UI']

class GameData:
	def __init__(self, artifact_descriptions=True):
		self.strings: dict[str, str] = {}
		self.artifacts: dict[str, dict] = {}
		self.artifact_names: dict[str, dict] = {}
		self.artifact_descriptions: dict[str, list[str]] = None
		self.artifact_attributes: dict[str, list[dict]] = None
		self.talents: dict = None

		for filename in TRANSLATION_FILES:
			with open('extracted/' + filename, 'r', encoding='utf-8') as f:
				self.strings.update(parse_translation(f))

		artifact_name_to_keys = collections.defaultdict(list)
		with open('extracted/ArtifactData', 'r', encoding='utf-8') as f:
			artifact_data = json.load(f)['Artifacts']
			for artifact in artifact_data:
				if not artifact.get('isDiscoverable', True): # airene's tower blessing
					continue
				try:
					name = self.resolve_string(artifact['ArtifactName'])
				except KeyError:
					continue
				key = artifact['Key']
				self.artifacts[key] = artifact
				if 'DropRate' in artifact:
					artifact['DropRate'] *= 1.7 # ArtifactDataController.LoadArtifactDataCO
				artifact_name_to_keys[name].append(key)
		for name, keys in artifact_name_to_keys.items():
			rarities = {self.artifacts[key].get('Rarity') for key in keys}
			(rarity,) = rarities
			key_list = []
			bases = []
			divinable = False
			for key in keys:
				artifact = self.artifacts[key]
				if artifact.get('isDivine'):
					divinable = True
				else:
					bases.append(artifact)
				key_list.append({'key': key, 'maxAnomaly': artifact.get('maxAnomaly')})
			if divinable:
				(base,) = bases # pylint: disable=unbalanced-tuple-unpacking
				base['isDivinable'] = True
			self.artifact_names[name] = {'keys': key_list, 'rarity': rarity}
		if artifact_descriptions:
			with open('extracted/artifact_descriptions.json', 'r', encoding='utf-8') as f:
				self.artifact_descriptions = json.load(f)

		with open('extracted/artifact_attributes.json', 'r', encoding='utf-8') as f:
			self.artifact_attributes: dict[list[list[dict]]] = json.load(f)

		material_names: dict[str, str] = {}
		with open('extracted/MaterialData', 'r', encoding='ascii') as f:
			for material in json.load(f)['Materials']:
				material_names[material['Key']] = self.strings[material['Name']]
		with open('extracted/runewords.json', 'r', encoding='ascii') as f:
			runewords: list[dict] = json.load(f)
		for runeword in runewords:
			key = ''.join(runeword['rune_key'])
			runes = [material_names[rune] for rune in runeword['rune_key']]
			self.artifacts[key] = {
				'ArtifactName': runeword['title'],
				'Key': key,
				'isRuneword': True,
				'Rarity': 3, # unique
				'specialDesc': True,
				'runes': runes,
			}
			name = self.strings[runeword['title']]
			self.artifact_names[name] = {'keys': [{'key': key, 'maxAnomaly': None}], 'rarity': None}
			self.artifact_attributes[key] = [runeword['attributes']]
			if artifact_descriptions:
				self.artifact_descriptions[key] = [runeword['special_desc']]

		with open('extracted/AttributesData', 'r', encoding='utf-8') as f:
			attr_data: dict[int, dict] = {}
			for attr in json.load(f)['ArtifactAttributes']:
				element = attr.get('associatedElement')
				if element is not None:
					element = DamageElement(element).name.lower()
				attr_data[attr['attributeType']] = {
					'element': element,
					'text': attr['text'],
					'postText': attr.get('postText'),
				}
			for anoms in self.artifact_attributes.values():
				for attr_list in anoms:
					for attr in attr_list:
						attr.update(attr_data[attr['type']])

		with open('extracted/LevelData', 'r', encoding='utf-8') as f:
			for level in json.load(f)['Levels']:
				for difficulty in level['Difficulties']:
					for key in difficulty['Loot']:
						self.artifacts[key]['droppedBossName'] = self.strings[level['Title']]
						difficulty_name = Difficulty(difficulty['Difficulty']).name.capitalize()
						self.artifacts[key]['droppedBossDifficulty'] = difficulty_name

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
		if re.fullmatch(r'\[[A-Z0-9_]+\]', value):
			value = self.strings[value[1:-1]]
		return value

	TOOLTIP_NAME_MAP = { # see UtilsManager.getTooltipByKey
		'ASCEND':              'UI_TOOLTIP_ACSEND_NAME',
		'BLOOD_LUST':          'UI_TOOLTIP_BLOODLUST_NAME',
		'ENERGY_DEPOT_CHARGE': 'UI_TOOLTIP_ENERGY_CHARGE_NAME',
		'FROST_METEOR':        'SKILL_FROST_METEOR_NAME',
		'WALL_OF_PAIN':        'ARTIFACT_WALL_OF_PAIN_NAME',
		'DAZE':                'RUNE_DAZE_NAME',
		'BULWARK':             'RUNE_BULWARK_NAME',
		'DECAYING_CORPSE':     'EFFECT_DECAYING_CORPSE_NAME',
	}

	def fetch_strings(self, s: str) -> dict[str, str]:
		extra_strings = {}
		for m in re.finditer(r'\[(\S+)\]', s):
			var = m.group(1)
			try:
				extra_strings[var] = self.strings[var]
			except KeyError:
				if var.startswith('LINK_'):
					base = var[len('LINK_'):]
					try:
						extra_strings[var] = self.strings[base + '_NAME']
					except KeyError:
						if base in self.TOOLTIP_NAME_MAP:
							extra_strings[var] = self.strings[self.TOOLTIP_NAME_MAP[base]]
						else:
							extra_strings[var] = self.strings['UI_TOOLTIP_%s_NAME' % base]
		return extra_strings

def parse_translation(f: typing.TextIO) -> dict[str, str]:
	strings: dict[str, str] = {}
	for line in f:
		if line in ('\n', 'END'):
			continue
		key, value = line.rstrip('\n').split('=', 1)
		if (key.startswith('SKILL_') or key.startswith('EFFECT_')) and key in strings:
			continue
		assert key not in strings, '%r seen twice' % key
		strings[key] = value
	return strings
