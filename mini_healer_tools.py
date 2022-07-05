#!/usr/bin/env python3

import sys
if len(sys.argv) == 3:
	import eventlet
	import eventlet.wsgi
	eventlet.monkey_patch()

# pylint: disable=wrong-import-position
import collections
import copy
import mimetypes
import json
import re

from pigwig import PigWig, Response
from pigwig.exceptions import HTTPException

def root(request):
	return Response.render(request, 'index.jinja2', {})

def artifacts_page(request, name=None):
	return Response.render(request, 'artifacts.jinja2', {})

def get_artifact_names(request):
	return Response.json(artifact_names)

def artifact(request, key):
	try:
		data = copy.copy(artifacts[key])
	except KeyError:
		raise HTTPException(404, '%r not found\n' % key)

	if 'ArtifactName' in data:
		data['ArtifactName'] = strings[data['ArtifactName']]
	if 'specialDesc' in data:
		data['specialDesc'] = strings[data['specialDesc']]
		data['strings'] = {}
		for m in re.finditer(r'\[(\S+)\]', data['specialDesc']):
			var = m.group(1)
			try:
				data['strings'][var] = strings[var]
			except KeyError:
				pass
	return Response.json(data)

def static(request, path):
	content_type, _ = mimetypes.guess_type(path)
	try:
		with open('static/' + path, 'rb') as f:
			return Response(f.read(), content_type=content_type)
	except FileNotFoundError:
		raise HTTPException(404, '%r not found\n' % path)

routes = [
	('GET', '/', root),
	('GET', '/artifacts', artifacts_page),
	('GET', '/artifacts/<name>', artifacts_page),
	('GET', '/data/artifact_names', get_artifact_names),
	('GET', '/data/artifact/<key>', artifact),
	('GET', '/static/<path:path>', static),
]

app = PigWig(routes, template_dir='html')
artifacts = strings = artifact_names = None

def main():
	global artifacts, strings, artifact_names
	strings = {}
	for filename in ['ARTIFACT', 'ATTRIBUTE', 'CONTEXT']:
		with open('extracted/' + filename, 'r', encoding='utf-8') as f:
			for line in f:
				if line == '\n' or line == 'END':
					continue
				key, value = line.rstrip('\n').split('=', 1)
				strings[key] = value
	with open('extracted/ArtifactData', 'r', encoding='utf-8') as f:
		artifact_data = json.load(f)['Artifacts']
		artifacts = {}
		artifact_names = collections.defaultdict(list)
		for artifact in artifact_data:
			try:
				name = strings[artifact['ArtifactName']]
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
