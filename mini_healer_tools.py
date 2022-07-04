#!/usr/bin/env python3

import sys
if len(sys.argv) == 3:
	import eventlet
	import eventlet.wsgi
	eventlet.monkey_patch()

# pylint: disable=wrong-import-position
import collections
import mimetypes
import json

from pigwig import PigWig, Response
from pigwig.exceptions import HTTPException

def root(request):
	with open('html/index.html', 'rb') as f:
		return Response(f.read(), content_type='text/html; charset=UTF-8')

def artifacts_page(request, name=None):
	with open('html/artifacts.html', 'rb') as f:
		return Response(f.read(), content_type='text/html; charset=UTF-8')

def get_artifact_names(request):
	return Response.json(artifact_names)

def artifact(request, key):
	try:
		return Response.json(artifacts[key])
	except KeyError:
		raise HTTPException(404, '%r not found\n' % key)

def static(request, path):
	content_type, _ = mimetypes.guess_type(path)
	with open('static/' + path, 'rb') as f:
		return Response(f.read(), content_type=content_type)

routes = [
	('GET', '/', root),
	('GET', '/artifacts/<name>', artifacts_page),
	('GET', '/data/artifact_names', get_artifact_names),
	('GET', '/data/artifact/<key>', artifact),
	('GET', '/static/<path:path>', static),
]

app = PigWig(routes)
artifacts = artifact_strings = artifact_names = None

def main():
	global artifacts, artifact_strings, artifact_names
	with open('extracted/ARTIFACT', 'r', encoding='utf-8') as f:
		artifact_strings = {}
		for line in f:
			if line == '\n' or line == 'END':
				continue
			key, value = line.rstrip('\n').split('=', 1)
			artifact_strings[key] = value
	with open('extracted/ArtifactData', 'r', encoding='utf-8') as f:
		artifact_data = json.load(f)['Artifacts']
		artifacts = {}
		artifact_names = collections.defaultdict(list)
		for artifact in artifact_data:
			try:
				name = artifact_strings[artifact['ArtifactName']]
			except KeyError:
				continue
			artifacts[artifact['Key']] = artifact
			artifact_names[name].append(artifact['Key'])

	if len(sys.argv) == 3:
		addr = sys.argv[1]
		port = int(sys.argv[2])
		eventlet.wsgi.server(eventlet.listen((addr, port)), app)
	else:
		app.main()

if __name__ == '__main__':
	main()
