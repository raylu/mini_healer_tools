#!/usr/bin/env python3

import json
import os
import os.path
import re
import subprocess
import sys
import urllib.request

import PIL.Image
import yaml

import extract_attributes
import extract_descriptions
import game_data

ASSETS_DIR = 'extracted/ExportedProject/Assets/'

def main():
	asset_ripper_path = sys.argv[1]
	dotnet_script_path = sys.argv[2]

	try:
		os.mkdir('extracted')
	except FileExistsError:
		pass

	if not os.path.exists('extracted/ExportedProject'):
		subprocess.run([asset_ripper_path, 'raw/', '-o', 'extracted'], check=True)

	for filename in game_data.TRANSLATION_FILES:
		path = 'extracted/ExportedProject/Assets/Resources/local/en_us/%s.txt' % filename
		os.link(path, 'extracted/' + filename)
	os.link(ASSETS_DIR + 'Resources/gamedata/artifact/ArtifactData.json',
			'extracted/ArtifactData')
	os.link(ASSETS_DIR + 'Resources/gamedata/attribute/AttributesData.json',
			'extracted/AttributesData')
	os.link(ASSETS_DIR + 'Resources/gamedata/talent/TalentData.json',
			'extracted/TalentData')
	os.link(ASSETS_DIR + 'Resources/fonts/raw/indienovaBC-Regular-12px.ttf',
			'extracted/indienovaBC-Regular-12px.ttf')
	os.link(ASSETS_DIR + 'Texture2D/Wisdom Tomes.png',
			'static/favicon.png')
	os.link(ASSETS_DIR + 'Texture2D/Frame.png',
			'static/artifact_frame.png')

	artifact_data = extract_artifacts()
	extract_talents()

	extract_attributes.extract_attributes(dotnet_script_path, artifact_data)
	data = game_data.GameData(artifact_descriptions=False)
	for artifact in artifact_data:
		try:
			artifact['specialDesc'] = data.resolve_string(artifact['specialDesc'])
		except KeyError:
			artifact['specialDesc'] = ''
	extract_descriptions.extract_descriptions(dotnet_script_path, artifact_data)

def extract_artifacts() -> dict:
	try:
		os.mkdir('static/artifacts')
	except FileExistsError:
		pass

	with open('extracted/ArtifactData', 'r', encoding='utf-8') as f:
		artifact_data = json.load(f)['Artifacts']

	icon_names: dict[str, str] = {} # "SIMPLE_SHIELD": "SimpleShiledIcon"
	with open(ASSETS_DIR + 'MonoScript/Assembly-CSharp/ArtifactDataController.cs', 'r', encoding='ascii') as f:
		active_keys: list[str] = None
		for line in f:
			keys = [m.group(1) for m in re.finditer(r'artifact.Key == "([A-Z_]+)"', line)]
			if keys:
				active_keys = keys
			else:
				m = re.search(r'artifact.Icon = (\w+);', line)
				if m:
					for key in active_keys: # pylint: disable=not-an-iterable
						icon_names[key] = m.group(1)

	image_guids: dict[str, str] = {} # "d599cf88e82d8c84ba650b2d80ab45d2": "Resources/image/artifacts/SIMPLESHIELD.png"
	for image_dir in ['Texture2D/', 'Resources/image/artifacts/']:
		for filename in os.listdir(ASSETS_DIR + image_dir):
			if not filename.endswith('.png.meta'):
				continue
			with open(ASSETS_DIR + image_dir + filename, 'r', encoding='utf-8') as f:
				assert f.readline() == 'fileFormatVersion: 2\n'
				guid_line = f.readline()
				assert guid_line.startswith('guid: ')
				guid = guid_line[len('guid: '):-1]
			image_guids[guid] = image_dir + filename[:-len('.meta')]
	with open(ASSETS_DIR + 'Scene/0_0_welcome.unity', 'r', encoding='utf-8') as f:
		for line in f:
			if line.endswith('artifactData:\n'):
				break
		else:
			raise Exception("couldn't find artifactData")
		lines = ['MonoBehaviour:\n']
		for line in f:
			if line.startswith('---'):
				break
			elif line.startswith('    '):
				continue
			lines.append(line)
	doc = yaml.safe_load(''.join(lines))
	icon_filenames: dict[str, str] = {} # "SimpleShiledIcon": Resources/image/artifacts/SIMPLESHIELD.png
	for k, v in doc['MonoBehaviour'].items():
		if (not k.endswith('Icon') and not k.endswith('icon')) or k == 'BleedIcon':
			continue
		assert v['fileID'] == 21300000 and v['type'] == 3, '%r: %r' % (k, v)
		filepath = image_guids.get(v['guid'])
		if filepath is not None:
			icon_filenames[k] = filepath

	for artifact in artifact_data:
		key: str = artifact['Key']
		output_path = 'static/artifacts/%s.png' % key

		if key == 'HOLLOWED_CORE_NORMAL': # this is the only item where the divine version isn't _DIVINE
			key = 'HOLLOWED_CORE'
		elif key in ('WISPERWIND', 'WISPERWIND_DIVINE'):
			key = 'WIND_WISPER'
		elif key in ('TOLMON_CRUELTY_N', 'TOLMON_CRUELTY_B'):
			key = 'TOLMONCRUELTY'
		elif key.endswith('_TOWER') and key != 'TRANQUIL_SPHERE_TOWER': # only tower item in ArtifactDataController.cs
			key = key[:-len('_TOWER')]

		try:
			filename = icon_filenames[icon_names[key]]
		except KeyError:
			pass
		else:
			os.link(ASSETS_DIR + filename, output_path)
			continue

		found = link_artifact_icon(key, output_path)
		if not found:
			if artifact.get('isDivine'):
				assert key.endswith('_DIVINE'), '%r is divine' % key
				key = key[:-len('_DIVINE')]
			for anom_suffix in ('_N', '_B', '_I'):
				if key.endswith(anom_suffix):
					key = key[:-len(anom_suffix)]
					break
			link_artifact_icon(key, output_path)

	return artifact_data

INPUT_DIRS = [
	ASSETS_DIR + 'Resources/image/artifacts/',
	ASSETS_DIR + 'Texture2D/',
]
def link_artifact_icon(key: str, output_path: str) -> bool:
	for input_dir in INPUT_DIRS:
		try:
			os.link(input_dir + key + '.png', output_path)
		except FileNotFoundError:
			pass
		else:
			return True
	try:
		os.link(ASSETS_DIR + 'Texture2D/%s.png' % pascal_case(key), output_path)
	except FileNotFoundError:
		return False
	else:
		return True

def pascal_case(s: str) -> str:
	"""IQSIOR_CAPE → IqsiorCape"""
	return ''.join(part.capitalize() for part in s.split('_'))

def extract_talents():
	url = 'https://gitlab.com/ezrast/mini-builder/-/raw/main/scripts/talent_fixups.json'
	with urllib.request.urlopen(url) as r:
		assert r.status == 200
		with open('extracted/talent_fixups.json', 'wb') as f:
			f.write(r.read())
	with open('extracted/talent_fixups.json', 'r', encoding='utf-8') as f:
		talent_fixups = json.load(f)

	with open('extracted/TALENT', 'r', encoding='utf-8') as f:
		talent_strings = game_data.parse_translation(f)
	with open('extracted/TalentData', 'r', encoding='utf-8') as f:
		talent_data = json.load(f)['Talents']

	try:
		os.mkdir('static/talents')
	except FileExistsError:
		pass
	for talent in talent_data:
		try:
			name = talent_strings[talent['TalentName']]
		except KeyError:
			continue
		output_path = 'static/talents/%s.png' % talent['Key']
		fixup = talent_fixups.get(name)
		if fixup is None or 'iconPath' not in fixup:
			os.link(ASSETS_DIR + 'Resources/image/talents/%s.png' % talent['Key'], output_path)
		else:
			icon_path = 'extracted/ExportedProject/' + fixup['iconPath']
			crop = fixup.get('iconCrop')
			if crop is None:
				os.link(icon_path, output_path)
			else:
				left, upper, width, height = crop
				with PIL.Image.open(icon_path) as image:
					icon = image.crop((left, upper, left+width, upper+height))
				icon.save(output_path)

if __name__ == '__main__':
	main()
