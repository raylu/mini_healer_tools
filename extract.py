#!/usr/bin/env python3

import json
import os
import os.path
import subprocess
import sys
import urllib.request

import PIL.Image

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

	extract_talents()

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
