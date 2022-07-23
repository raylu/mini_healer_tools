#!/usr/bin/env python3

import json
import os
import os.path
import subprocess
import sys
import urllib.request

import PIL.Image
import yaml

import game_data

def main():
	asset_ripper_path = sys.argv[1]

	try:
		os.mkdir('extracted')
	except FileExistsError:
		pass

	if not os.path.exists('extracted/ExportedProject'):
		subprocess.run([asset_ripper_path, 'raw/', '-o', 'extracted'], check=True)

	for filename in ['ARTIFACT', 'ATTRIBUTE', 'CONTEXT', 'TALENT']:
		path = 'extracted/ExportedProject/Assets/Resources/local/en_us/%s.txt' % filename
		os.link(path, 'extracted/' + filename)
	os.link('extracted/ExportedProject/Assets/Resources/gamedata/artifact/ArtifactData.json',
			'extracted/ArtifactData')
	os.link('extracted/ExportedProject/Assets/Resources/gamedata/talent/TalentData.json',
			'extracted/TalentData')
	os.link('extracted/ExportedProject/Assets/Resources/fonts/raw/indienovaBC-Regular-12px.ttf',
			'extracted/indienovaBC-Regular-12px.ttf')
	os.link('extracted/ExportedProject/Assets/Texture2D/Wisdom Tomes.png',
			'static/favicon.png')

	extract_artifacts()
	extract_talents()

def extract_artifacts():
	try:
		os.mkdir('static/artifacts')
	except FileExistsError:
		pass

	with open('extracted/ArtifactData', 'r', encoding='utf-8') as f:
		artifact_data = json.load(f)['Artifacts']

	image_guids: dict[str, str] = {}
	texture_dir = 'extracted/ExportedProject/Assets/Texture2D/'
	for filename in os.listdir(texture_dir):
		if not filename.endswith('.png.meta'):
			continue
		with open(texture_dir + filename, 'r', encoding='utf-8') as f:
			assert f.readline() == 'fileFormatVersion: 2\n'
			guid_line = f.readline()
			assert guid_line.startswith('guid: ')
			guid = guid_line[len('guid: '):-1]
		image_guids[guid] = filename[:-len('.png.meta')]
	with open('extracted/ExportedProject/Assets/Scene/0_0_welcome.unity', 'r', encoding='utf-8') as f:
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
	icon_filenames: dict[str, str] = {}
	for k, v in doc['MonoBehaviour'].items():
		if not k.endswith('Icon') or k == 'BleedIcon':
			continue
		assert v['fileID'] == 21300000 and v['type'] == 3, '%r: %r' % (k, v)
		filename = image_guids.get(v['guid'])
		if filename is not None:
			icon_filenames[k[:-len('Icon')]] = filename

	for artifact in artifact_data:
		key: str = artifact['Key']
		output_path = 'static/artifacts/%s.png' % key

		filename = icon_filenames.get(pascal_case(key))
		if filename is not None:
			os.link(texture_dir + filename + '.png', output_path)
			continue

		if key == 'HOLLOWED_CORE_NORMAL': # this is the only item where the divine version isn't _DIVINE
			key = 'HOLLOWED_CORE'
		elif key in ('WISPERWIND', 'WISPERWIND_DIVINE'):
			key = 'WIND_WISPER'
		found = link_artifact_icon(key, output_path)
		if not found:
			if artifact.get('isDivine'):
				assert key.endswith('_DIVINE'), '%r is divine' % key
				key = key[:-len('_DIVINE')]
			for anom_suffix in ('_N', '_B', '_I'):
				if key.endswith(anom_suffix):
					key = key[:-len(anom_suffix)]
					break
			found = link_artifact_icon(key, output_path)
		if not found:
			print(key)

INPUT_DIRS = [
	'extracted/ExportedProject/Assets/Resources/image/artifacts/',
	'extracted/ExportedProject/Assets/Texture2D/',
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
		os.link('extracted/ExportedProject/Assets/Texture2D/%s.png' % pascal_case(key), output_path)
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
			os.link('extracted/ExportedProject/Assets/Resources/image/talents/%s.png' % talent['Key'], output_path)
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
