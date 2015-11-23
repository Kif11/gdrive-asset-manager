import os
import sys
sys.path.insert(1, os.path.join(os.getcwd(), 'venv/Lib/site-packages'))
import json
from pathlib import Path
from drive import DriveFile
from drive import LocalFile

PACKAGE_PATH = 'C:/Users/kkirill2/Desktop/SQ02_SH010'
PACKAGE_FILE_PATH = PACKAGE_PATH + '/shot.json'
PROJECT_DIR = Path('C:/Users/kkirill2/Desktop/BirdKeeper')


class ShotPackage (object):
	def __init__(self):
		pass
	def _read_package_file(self, pfile):
		"""
		returns: JSON object
		"""
		with open(pfile, 'r') as f:
			data = f.read()
		return json.loads(data)

	def _creat_path(self, path):
	    sub_path = os.path.dirname(path)
	    if not os.path.exists(sub_path):
	        self._creat_path(sub_path)
	    if not os.path.exists(path):
	        os.mkdir(path)
	
	def download(self):
		shot = self._read_package_file(PACKAGE_FILE_PATH)
		for f in shot['files']:
			dfile = DriveFile(f['id'])
			dpath = dfile.get_path().relative_to('/My Drive/Bird Keeper/PostProd')
			file_dir = PROJECT_DIR / dpath
			self._creat_path(str(file_dir))

			dfile.download(LocalFile(file_dir))

if __name__ == '__main__':
	s = ShotPackage()
	s.download()