#!/usr/bin/env python3

import io
import re
import textwrap

import httpx
import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont
from export_image import ARTIFACT_WIDTH

import game_data
import wiki_creds

def main():
	r = api_request('get', params={
		'action': 'query',
		'meta': 'tokens',
		'type': 'login',
		'format': 'json',
	})
	login_token = r.json()['query']['tokens']['logintoken']

	r = api_request('post', data={
		'action': 'login',
		'lgname': wiki_creds.username,
		'lgpassword': wiki_creds.password,
		'lgtoken': login_token,
		'format': 'json',
	})

	r = api_request('get', params={
		'action': 'query',
		'meta': 'tokens',
		'format': 'json',
	})
	csrf_token = r.json()['query']['tokens']['csrftoken']

	data = game_data.GameData()
	for name, artifacts in data.artifact_names.items():
		if name in ['Combustion', 'Solarflare', 'Thundercrack']:
			continue
		create_page(data, csrf_token, name, artifacts)

def create_page(data: game_data.GameData, csrf_token: str, name: str, artifacts: dict):
	filenames: list[str] = []
	for key in artifacts['keys']:
		max_anomaly = key.get('maxAnomaly') or 0
		for anomaly in range(max_anomaly + 1):
			b = render_artifact(data, key['key'], anomaly)
			b.seek(0)
			filename = key['key']
			if anomaly > 0:
				filename += '_ANOMALY%d' % anomaly
			filename += '.png'
			api_request('post', data={
				'action': 'upload',
				'filename': filename,
				'comment': 'automatically created via github.com/raylu/mini_healer_tools',
				'token': csrf_token,
				#'ignorewarnings': 1, # replace existing images
				'format': 'json',
			}, files={'file': b})
			filenames.append(filename)

	artifact = data.artifacts[artifacts['keys'][0]['key']]
	categories = ['Artifacts']
	if artifact.get('isRuneword'):
		categories.append('Runeword')
	else:
		item_type = game_data.Types(artifact['Type']).name.replace('_', ' ').title()
		categories.append(item_type)
		rarity = game_data.Rarities(artifact['Rarity']).name.capitalize()
	if artifact.get('isDepth'):
		categories.append('Depth')

	text = '<gallery>\n'
	text += '\n'.join('File:%s' % filename for filename in filenames)
	text += '\n</gallery>'
	text += '\n\n{{PAGENAME}} is a '
	if artifact.get('isRuneword'):
		text += '[[Runeword]]'
	else:
		text += '%s %s' % (rarity, item_type)
		if 'droppedBossName' in artifact:
			if artifact.get('isDepth'):
				text += ' that drops in ' + artifact['droppedZone']
			else:
				text += ' that drops from [[%s]] on %s' % (
						artifact['droppedBossName'], artifact['droppedBossDifficulty'])
	text += '.'
	text += '\n\n==Mechanics==\n\n==Interactions with Talents=='
	text += '\n\n==Interactions with Artifacts==\n\n----\n{{Uniques Navbox}}\n'
	text += '\n'.join('[[Category:%s]]' % category for category in categories)

	print(name, filenames)
	r = api_request('post', data={
		'action': 'edit',
		'title': name,
		'text': text,
		'summary': 'automatically created via github.com/raylu/mini_healer_tools',
		'createonly': 1,
		'bot': 1,
		'token': csrf_token,
		'format': 'json',
	})

client = httpx.Client()
def api_request(method: str, **kwargs) -> httpx.Response:
	r = client.request(method, 'https://minihealer.fandom.com/api.php', timeout=10, **kwargs)
	r.raise_for_status()
	return r

ARTIFACT_WIDTH = 480
ICON_SIZE = 30
ELEMENT_COLORS = {
	'phsyical': (0xbc, 0xbc, 0xbc),
	'fire': (0xff, 0x33, 0x33),
	'ice': (0x69, 0x83, 0xff),
	'lightning': (0xef, 0xd7, 0x3c),
	'nemesis': (0xce, 0x31, 0xc3),
}
def render_artifact(data: game_data.GameData, key: str, anomaly: int) -> io.BytesIO:
	image = PIL.Image.new('RGB', (ARTIFACT_WIDTH, 1000))
	draw = PIL.ImageDraw.Draw(image)
	font = PIL.ImageFont.truetype('extracted/NormalTextPixelFont.ttf', 24)
	big_font = PIL.ImageFont.truetype('extracted/NormalTextPixelFont.ttf', 30)

	with PIL.Image.open('static/artifact_frame.png') as frame:
		image.paste(frame.resize((100, 100)), (ARTIFACT_WIDTH // 2 - 100 // 2, 0))

	artifact = data.artifacts[key]
	if artifact.get('isRuneword'):
		icon_filepath = 'static/runes.png'
	else:
		icon_filename = artifact['Key']
		if anomaly:
			icon_filename += '_ANOMALY%d' % anomaly
		icon_filepath = 'static/artifacts/%s.png' % icon_filename
	with PIL.Image.open(icon_filepath) as icon:
		resized = icon.resize((64, 64))
		image.paste(resized, (ARTIFACT_WIDTH // 2 - 64 // 2, 16), resized)

	name = data.resolve_string(artifact['ArtifactName'])
	draw.text((ARTIFACT_WIDTH // 2, 120), name, (158, 124, 46), big_font, 'mt')

	icons = []
	if artifact.get('isChaotic'):
		icons.append('chaotic')
	if artifact.get('isDivine'):
		icons.append('divine')
	elif artifact.get('isDivinable'):
		icons.append('divinable')
	if anomaly > 0:
		icons.append('anomalous')
	icon_y_offset = 100
	for icon_name in icons:
		pos = ((0, icon_y_offset), (ICON_SIZE, icon_y_offset + ICON_SIZE))
		draw.rounded_rectangle(pos, outline=(187, 153, 136), radius=2)
		with PIL.Image.open('static/artifact_%s.png' % icon_name) as icon:
			resized = icon.resize((ICON_SIZE, ICON_SIZE))
			image.paste(resized, (1, icon_y_offset + 1), resized)
		icon_y_offset += ICON_SIZE + 4

	types: list[str] = []
	if artifact.get('isRuneword'):
		types.append('Runic')
	else:
		types.append(game_data.Types(artifact['Type']).name.capitalize())
		types.append(game_data.Rarities(artifact['Rarity']).name.capitalize())
	if artifact.get('isUltraRare'):
		types.append('Ultra Rare')
	if artifact.get('isChaotic'):
		types.append('Chaotic')
	types_str = '(%s)' % ', '.join(types)
	draw.text((ARTIFACT_WIDTH // 2, 155), types_str, (119, 119, 119), font, 'mt')

	y_offset = 200
	for attr in data.artifact_attributes[artifact['Key']][anomaly]:
		if attr['text'] == 'ATTRIBUTE_TALENT_LEVEL_TEXT':
			text = data.resolve_string('TALENT_%s_NAME' % attr['ref_id'])
		else:
			text = data.resolve_string(attr['text'])

		sign = '+'
		if attr['is_negative']:
			sign = ''
		number = str(attr['t1_min'])
		if attr['t1_min'] != attr['t1_max']:
			number = '%d to %d' % (attr['t1_min'], attr['t1_max'])
		attribute = translate_string(data, text)
		line = sign + number
		if attribute[0] != '%':
			line += ' '
		line += attribute
		if attr['postText'] is not None:
			line += ' ' + data.resolve_string(attr['postText'])

		if attr['ref_id']: # link
			color = (0, 170, 170)
		elif attr['attribute'] in ('INCREASE_HEALPOWER_FLAT', 'INCREASE_HEALPOWER_PERCENT'): # healpower
			color = (0xd6, 0x60, 0xaf)
		elif attr['element'] is not None:
			color = ELEMENT_COLORS[attr['element']]
		else:
			color = (209, 209, 209)
		y_offset = render_line(draw, font, y_offset, line, color)

	if 'specialDesc' in artifact:
		y_offset += 28
		for desc in data.artifact_descriptions[artifact['Key']][anomaly]:
			for orig_line in desc.split('<br>'):
				desc = translate_string(data, orig_line)
				y_offset = render_line(draw, font, y_offset, desc, (209, 209, 209))

	output = io.BytesIO()
	image.crop((0, 0, ARTIFACT_WIDTH, y_offset)).save(output, 'png')
	return output

def translate_string(data: game_data.GameData, s: str) -> str:
	for m in re.finditer(r'\[(\S+)\]', s):
		var = m.group(1)
		try:
			resolved = data.strings[var]
		except KeyError:
			if var.startswith('LINK_'):
				base = var[len('LINK_'):]
				try:
					resolved = data.strings[base + '_NAME']
				except KeyError:
					if base in data.TOOLTIP_NAME_MAP:
						resolved = data.strings[data.TOOLTIP_NAME_MAP[base]]
					else:
						resolved = data.strings['UI_TOOLTIP_%s_NAME' % base]
		s = s.replace('[%s]' % var, resolved)
	return s

def render_line(draw: PIL.ImageDraw.ImageDraw, font: PIL.ImageFont.ImageFont, y_offset: int,
		s: str, color: tuple[int, int, int]) -> int:
	if s == '':
		y_offset += 28 # textwrap.wrap('') doesn't yield anything
	else:
		for line in textwrap.wrap(s, 32):
			draw.text((ICON_SIZE, y_offset), line, color, font, 'lt')
			y_offset += 28
	return y_offset

if __name__ == '__main__':
	import sys
	if sys.argv[1] == 'preview':
		with open('artifact_image.png', 'wb') as f:
			f.write(render_artifact(game_data.GameData(), sys.argv[2], int(sys.argv[3])).getvalue())
	elif sys.argv[1] == 'create':
		main()
