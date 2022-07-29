#!/usr/bin/env python3

import io
import re

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
	print('login token is %r' % login_token)

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

	with open('static/artifacts/AURAMANCER_STONE.png', 'rb') as f:
		r = api_request('post', data={
			'action': 'upload',
			'filename': 'AURAMANCER_STONE.png',
			'comment': 'automatically created via github.com/raylu/mini_healer_tools',
			'token': csrf_token,
			'format': 'json',
		}, files={'file': f})
		print(r.text)

client = httpx.Client()
def api_request(method: str, **kwargs) -> httpx.Response:
	r = client.request(method, 'https://minihealer.fandom.com/api.php', **kwargs)
	r.raise_for_status()
	return r

ARTIFACT_WIDTH = 460
ELEMENT_COLORS = {
	'phsyical': (0xbc, 0xbc, 0xbc),
	'fire': (0xff, 0x33, 0x33),
	'ice': (0x69, 0x83, 0xff),
	'lightning': (0xef, 0xd7, 0x3c),
	'nemesis': (0xce, 0x31, 0xc3),
}
def render_artifact(artifact: dict, anomaly: int) -> io.BytesIO:
	image = PIL.Image.new('RGB', (ARTIFACT_WIDTH, 1000))
	draw = PIL.ImageDraw.Draw(image)
	font = PIL.ImageFont.truetype('extracted/NormalTextPixelFont.ttf', 24)

	with PIL.Image.open('static/artifact_frame.png') as frame:
		image.paste(frame.resize((96, 96)), (ARTIFACT_WIDTH // 2 - 96 // 2, 0))

	if artifact.get('isRuneword'):
		icon_filepath = 'static/runes.png'
	else:
		icon_filename = artifact['Key']
		if anomaly:
			icon_filename += '_ANOMALY%d' % anomaly
		icon_filepath = 'static/artifacts/%s.png' % icon_filename
	with PIL.Image.open(icon_filepath) as icon:
		resized = icon.resize((64, 64))
		image.paste(resized, (ARTIFACT_WIDTH // 2 - 64 // 2, 12), resized)

	name = data.resolve_string(artifact['ArtifactName'])
	draw.text((ARTIFACT_WIDTH // 2, 120), name, (158, 124, 46), font, 'mt')

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
	draw.text((ARTIFACT_WIDTH // 2, 150), types_str, (119, 119, 119), font, 'mt')

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
		attribute = render_string(data, text)
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
		draw.text((0, y_offset), line, color, font, 'lt')
		y_offset += 28

	output = io.BytesIO()
	image.save(output, 'webp')
	return output

def render_string(data: game_data.GameData, s: str) -> str:
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

if __name__ == '__main__':
	data = game_data.GameData()
	b = render_artifact(data.artifacts['AURAMANCER_STONE'], 0)
	with open('artifact_image.png', 'wb') as f:
		f.write(b.getvalue())
