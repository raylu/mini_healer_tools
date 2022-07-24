#!/usr/bin/env python3

import sys
if len(sys.argv) == 3:
	import eventlet
	import eventlet.wsgi
	eventlet.monkey_patch()

# pylint: disable=wrong-import-position
import copy
import json
import mimetypes

from pigwig import PigWig, Response
from pigwig.exceptions import HTTPException

import export_image
import game_data

def root(request):
	return Response.render(request, 'index.jinja2', {})

def artifacts_page(request, name=None):
	return Response.render(request, 'artifacts.jinja2', {})

def build_page(request, name=None):
	return Response.render(request, 'build.jinja2', {})

def export_build(request):
	body, body_len = request.body
	expected = b'build='
	field = body.read(len(expected))
	assert field == expected, 'expected %r but got %r' % (expected, field)
	build = json.loads(body.read(body_len - len(expected)))
	image_bytes = export_image.export_build(data, build)
	return Response(image_bytes.getvalue(), content_type='image/webp')

def get_artifact_names(request):
	return Response.json(data.artifact_names)

def get_artifact(request, key):
	try:
		artifact = copy.copy(data.artifacts[key])
	except KeyError:
		raise HTTPException(404, '%r not found\n' % key) # pylint: disable=raise-missing-from

	if 'ArtifactName' in artifact:
		artifact['ArtifactName'] = data.resolve_string(artifact['ArtifactName'])
	if 'specialDesc' in artifact:
		artifact['specialDesc'] = '<br>'.join(data.artifact_descriptions[artifact['Key']])
		artifact['strings'] = data.fetch_strings(artifact['specialDesc'])
	return Response.json(artifact)

def get_talents(request):
	return Response.json(data.talents)

def static(request, path):
	content_type, _ = mimetypes.guess_type(path)
	try:
		with open('static/' + path, 'rb') as f:
			return Response(f.read(), content_type=content_type)
	except FileNotFoundError:
		raise HTTPException(404, '%r not found\n' % path) # pylint: disable=raise-missing-from

routes = [
	('GET', '/', root),
	('GET', '/artifacts', artifacts_page),
	('GET', '/artifacts/<name>', artifacts_page),
	('GET', '/build', build_page),
	('POST', '/build/export', export_build),
	('GET', '/data/artifact_names', get_artifact_names),
	('GET', '/data/artifact/<key>', get_artifact),
	('GET', '/data/talents', get_talents),
	('GET', '/static/<path:path>', static),
]

app = PigWig(routes, template_dir='html')
data = game_data.GameData()

def main():
	if len(sys.argv) == 3:
		addr = sys.argv[1]
		port = int(sys.argv[2])
		eventlet.wsgi.server(eventlet.listen((addr, port)), app)
	else:
		app.main()

if __name__ == '__main__':
	main()
