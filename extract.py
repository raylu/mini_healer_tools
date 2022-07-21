#!/usr/bin/env python3

import os
import subprocess
import sys

def main():
	asset_ripper_path = sys.argv[1]

	try:
		os.mkdir('extracted')
	except FileExistsError:
		pass

	subprocess.run([asset_ripper_path, 'raw/', '-o' 'extracted'], check=True)

if __name__ == '__main__':
	main()
