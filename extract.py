#!/usr/bin/env python3

import json
import os
import subprocess
import sys
import urllib.request

def main():
	asset_ripper_path = sys.argv[1]

	try:
		os.mkdir('extracted')
	except FileExistsError:
		pass

	subprocess.run([asset_ripper_path, 'raw/', '-o', 'extracted'], check=True)

	for filename in ['ARTIFACT', 'ATTRIBUTE', 'CONTEXT', 'TALENT']:
		path = 'extracted/ExportedProject/Assets/Resources/local/en_us/%s.txt' % filename
		os.link(path, 'extracted/' + filename)
	os.link('extracted/ExportedProject/Assets/Resources/gamedata/artifact/ArtifactData.json',
			'extracted/ArtifactData')
	os.link('extracted/ExportedProject/Assets/Resources/gamedata/talent/TalentData.json',
			'extracted/TalentData')

	url = 'https://gitlab.com/ezrast/mini-builder/-/raw/main/scripts/talent_fixups.json'
	with urllib.request.urlopen(url) as r:
		assert r.status == 200
		with open('extracted/talent_fixups.json', 'wb') as f:
			f.write(r.read())
	with open('extracted/talent_fixups.json', 'r', encoding='utf-8') as f:
		talent_fixups = json.load(f)

	with open('extracted/TALENT', 'r', encoding='utf-8') as f:
		talent_strings: dict[str, str] = {}
		for line in f:
			if line in ('\n', 'END'):
				continue
			key, value = line.rstrip('\n').split('=', 1)
			assert key not in talent_strings
			talent_strings[key] = value
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
		try:
			fixup = talent_fixups[name]
			icon_path = fixup['iconPath']
		except KeyError:
			icon_path = 'Assets/Resources/image/talents/%s.png' % talent['Key']
		os.link('extracted/ExportedProject/' + icon_path, 'static/talents/%s.png' % talent['Key'])

if __name__ == '__main__':
	main()
