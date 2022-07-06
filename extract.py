#!/usr/bin/env python3

import os
import struct

def main():
	try:
		os.mkdir('extracted')
	except FileExistsError:
		pass

	files = [
		('ArtifactData', 0x200),
		('SkillData', 0x200),
		('TalentData', 0x200),
		('AttributesData', 0x200),
		('Bosses', 0x200),
		('skill_info', 0x200),
		('AT', 0x06e460b8),
		('ATTRIBUTE', 0x06d8a090),
		('ARTIFACT', 0x06e493e0),
		('CONTEXT', 0x06e882b0),
		('TALENT', 0x06c0d6f0),
	]
	with open('raw/resources.assets', 'rb') as asset_f:
		for filename, offset in files:
			print('extracting', filename)
			d = read_file(asset_f, filename.encode('ascii'), offset)
			with open('extracted/' + filename, 'w') as extracted_f:
				extracted_f.write(d.decode('utf-8'))

def read_file(f, filename, offset):
	f.seek(offset, os.SEEK_SET)
	while True:
		buf = f.read(512 * 1024)
		buf_offset = buf.find(b'\x00' * 2 + filename)
		if buf_offset == -1 or buf_offset % 4 != 2:
			f.seek(-32, os.SEEK_CUR)
			offset += 512 * 1024 - 32
		else:
			offset += 2 + buf_offset
			break

	pad_bytes = (len(filename) + 3) // 4 * 4 - len(filename)
	null_padding = b'\x00' * pad_bytes
	f.seek(offset, os.SEEK_SET)
	assert f.read(len(filename)+ pad_bytes) == filename + null_padding
	(asset_len,) = struct.unpack('I', f.read(4))
	return f.read(asset_len)


if __name__ == '__main__':
	main()
