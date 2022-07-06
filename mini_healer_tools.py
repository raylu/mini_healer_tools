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

def build_page(request, name=None):
	return Response.render(request, 'build.jinja2', {})

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
		data['strings'] = _fetch_strings(data['specialDesc'])
	return Response.json(data)

def get_talents(request):
	return Response.json(talents)

def static(request, path):
	content_type, _ = mimetypes.guess_type(path)
	try:
		with open('static/' + path, 'rb') as f:
			return Response(f.read(), content_type=content_type)
	except FileNotFoundError:
		raise HTTPException(404, '%r not found\n' % path)

def _fetch_strings(s):
	extra_strings = {}
	for m in re.finditer(r'\[(\S+)\]', s):
		var = m.group(1)
		try:
			extra_strings[var] = strings[var]
		except KeyError:
			pass
	return extra_strings

routes = [
	('GET', '/', root),
	('GET', '/artifacts', artifacts_page),
	('GET', '/artifacts/<name>', artifacts_page),
	('GET', '/build', build_page),
	('GET', '/data/artifact_names', get_artifact_names),
	('GET', '/data/artifact/<key>', artifact),
	('GET', '/data/talents', get_talents),
	('GET', '/static/<path:path>', static),
]

app = PigWig(routes, template_dir='html')
artifacts = strings = artifact_names = talents = None

def main():
	global artifacts, strings, artifact_names, talents
	strings = {}
	for filename in ['ARTIFACT', 'ATTRIBUTE', 'CONTEXT', 'TALENT']:
		with open('extracted/' + filename, 'r', encoding='utf-8') as f:
			for line in f:
				if line == '\n' or line == 'END':
					continue
				key, value = line.rstrip('\n').split('=', 1)
				assert key not in strings
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
	with open('extracted/TalentData', 'r', encoding='utf-8') as f:
		talent_data = json.load(f)['Talents']
		talent_dict = {}
		talent_strings = {}
		for talent in talent_data:
			try:
				talent['TalentName'] = strings[talent['TalentName']]
			except KeyError:
				continue
			key = talent['Key']
			talent['desc'] = strings.get('TALENT_%s_DESC' % key)
			if talent['desc'] is not None:
				talent_strings.update(_fetch_strings(talent['desc']))
			talent_dict[key] = talent
		talents = {'talents': talent_dict, 'strings': talent_strings}

	if len(sys.argv) == 3:
		addr = sys.argv[1]
		port = int(sys.argv[2])
		eventlet.wsgi.server(eventlet.listen((addr, port)), app)
	else:
		app.main()

if __name__ == '__main__':
	main()
