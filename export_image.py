import ctypes
import io

import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont

import game_data

ROW_HEIGHT = 50
COLUMN_WIDTH = 38
TREE_GAP_WIDTH = 40
ARTIFACT_WIDTH = 375

def export_build(data: game_data.GameData, build: dict) -> io.BytesIO:
	# parse talents from URL keys
	classes = dict.fromkeys(game_data.TalentClass, False)
	selected_talents = {int(url_key_str): count for url_key_str, count in build['talents'].items()}
	for url_key_int, count in selected_talents.items():
		url_key = URLKey()
		url_key.bytes = url_key_int # pylint: disable=attribute-defined-outside-init
		classes[url_key.bits.class_] = True

	num_classes = sum(classes.values())
	trees_width = COLUMN_WIDTH * 5 * num_classes + (TREE_GAP_WIDTH - 1) * num_classes
	artifacts_width = 0
	if len(build['items']) > 0:
		artifacts_width = ARTIFACT_WIDTH
	image = PIL.Image.new('RGB', (trees_width + artifacts_width, ROW_HEIGHT * 10 - 4))

	talent_font = PIL.ImageFont.truetype('extracted/indienovaBC-Regular-12px.ttf', 12)
	x_offset = 0
	for class_ in game_data.TalentClass:
		if not classes[class_]:
			continue
		image.paste(_draw_tree(data, class_, selected_talents, talent_font), (x_offset, 0))
		x_offset += COLUMN_WIDTH * 5 + TREE_GAP_WIDTH

	image.paste(_draw_artifacts(data, build['items']), (trees_width + 10, 0))

	output = io.BytesIO()
	image.save(output, 'webp')
	return output

def _draw_tree(data: game_data.GameData, class_: game_data.TalentClass, selected_talents: dict[int, int],
		font: PIL.ImageFont.ImageFont) -> PIL.Image.Image:
	image = PIL.Image.new('RGB', (COLUMN_WIDTH * 5 - 2, ROW_HEIGHT * 10 - 4))
	draw = PIL.ImageDraw.Draw(image)
	for talent in data.talents['talents'].values():
		if talent['Type'] != class_:
			continue
		url_key = URLKey()
		url_key.bits.class_ = talent['Type']
		url_key.bits.tier = talent['tier']
		url_key.bits.position = talent['Position']
		count = selected_talents.get(url_key.bytes, 0)

		pos = (url_key.bits.position * COLUMN_WIDTH, (url_key.bits.tier-1) * ROW_HEIGHT)
		with PIL.Image.open('static/talents/%s.png' % talent['Key']) as icon:
			image.paste(icon.resize((32, 32)), pos)
		draw.rectangle((pos, (pos[0] + 34, pos[1] + 45)), outline=(119, 85, 85))
		text_color = (170, 170, 170)
		if count > 0:
			fill = (119, 85, 85)
			if count == talent['maxLevel']:
				fill = (58, 153, 85)
			draw.rectangle(((pos[0], pos[1] + 33), (pos[0] + 34, pos[1] + 45)), fill=fill)
			text_color = (221, 221, 221)
		draw.text((pos[0] + 18, pos[1] + 35), str(count), text_color, font, 'mt')
	return image

def _draw_artifacts(data: game_data.GameData, items: list[list]) -> PIL.Image.Image:
	image = PIL.Image.new('RGB', (ARTIFACT_WIDTH, ROW_HEIGHT * 10))
	draw = PIL.ImageDraw.Draw(image)
	font = PIL.ImageFont.truetype('extracted/NormalTextPixelFont.ttf', 18)

	with PIL.Image.open('static/artifact_frame.png') as frame_orig:
		frame = frame_orig.resize((56, 56))

	y_offset = 8
	for key, anomaly in items:
		artifact = data.artifacts[key]

		image.paste(frame, (0, y_offset))
		if artifact.get('isRuneword'):
			icon_filepath = 'static/runes.png'
		else:
			icon_filename = artifact['Key']
			if anomaly:
				icon_filename += '_ANOMALY%d' % anomaly
			icon_filepath = 'static/artifacts/%s.png' % icon_filename
		with PIL.Image.open(icon_filepath) as icon:
			resized = icon.resize((32, 32))
			image.paste(resized, (12, y_offset + 12), resized)

		name = data.resolve_string(artifact['ArtifactName'])
		draw.text((72, y_offset + 20), name, (158, 124, 46), font, 'lt')
		y_offset += 64

	return image

c_uint16 = ctypes.c_uint16
class URLKeyBits(ctypes.LittleEndianStructure):
	_fields_ = [
		('position', c_uint16, 3),
		('tier', c_uint16, 4),
		('class_', c_uint16, 3),
	]

class URLKey(ctypes.Union):
	_fields_ = [('bits', URLKeyBits), ('bytes', c_uint16)]
