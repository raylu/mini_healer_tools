import ctypes
import io

import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont

import game_data

ROW_HEIGHT = 50
COLUMN_WIDTH = 38
TREE_GAP_WIDTH = 40

def export_build(data: game_data.GameData, build: dict) -> io.BytesIO:
	# parse talents from URL keys
	classes = dict.fromkeys(game_data.TalentClass, False)
	selected_talents = {int(url_key_str): count for url_key_str, count in build['talents'].items()}
	for url_key_int, count in selected_talents.items():
		url_key = URLKey()
		url_key.bytes = url_key_int # pylint: disable=attribute-defined-outside-init
		classes[url_key.bits.class_] = True

	num_classes = sum(classes.values())
	image = PIL.Image.new('RGB',
		(COLUMN_WIDTH * 5 * num_classes + TREE_GAP_WIDTH * (num_classes - 1) - 3, ROW_HEIGHT * 10 - 4))
	font = PIL.ImageFont.truetype('extracted/indienovaBC-Regular-12px.ttf', 12)
	x_offset = 0
	for class_ in game_data.TalentClass:
		if not classes[class_]:
			continue
		image.paste(_draw_tree(data, class_, selected_talents, font), (x_offset, 0))
		x_offset += COLUMN_WIDTH * 5 + TREE_GAP_WIDTH

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

c_uint16 = ctypes.c_uint16
class URLKeyBits(ctypes.LittleEndianStructure):
	_fields_ = [
		('position', c_uint16, 3),
		('tier', c_uint16, 4),
		('class_', c_uint16, 3),
	]

class URLKey(ctypes.Union):
	_fields_ = [('bits', URLKeyBits), ('bytes', c_uint16)]
