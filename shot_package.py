import os
import sys
sys.path.insert(1, os.path.join(os.getcwd(), 'venv/Lib/site-packages'))
import json
from pathlib import Path
from drive import DriveFile
from drive import LocalFile

PACKAGE_PATH = 'C:/Users/kkirill2/Desktop/BirdKeeper'
PACKAGE_FILE_PATH = PACKAGE_PATH + '/package.json'
PROJECT_DIR = Path('C:/Users/kkirill2/Desktop/BirdKeeper')


class ShotPackage (object):
	def __init__(self):
		self.package = self._read_package_file()

	def _read_package_file(self):
		"""
		returns: JSON object
		"""
		with open(PACKAGE_FILE_PATH, 'r') as f:
			data = f.read()
		return json.loads(data)

	def _create_path(self, path):
	    sub_path = os.path.dirname(path)
	    if not os.path.exists(sub_path):
	        self._create_path(sub_path)
	    if not os.path.exists(path):
	        os.mkdir(path)

	def _sync_local_package(self):
		with open(PACKAGE_FILE_PATH, 'w') as f:
			json.dump(self.package, f, indent=4, sort_keys=True)

	def _download(self, dfile):
		
		dpath = dfile.get_path().relative_to('/My Drive/Bird Keeper/PostProd')
		fname = dfile.name()
		file_dir = PROJECT_DIR / dpath
		file_path = file_dir / fname
		
		if not file_dir.exists():
			self._create_path(str(file_dir))

		dfile.download(LocalFile(file_path))

		# TODO(kirill): This is just simple check for now.
		# We need to fo a check for outdated file and if so replace it.
		# if not file_path.exists():
		# 	dfile.download(LocalFile(file_path))
		# else:
		# 	print fname, 'File already exists'
	
	def sync(self):
		
		for entity in self.package:
			for f in entity['files']:
				dfile = DriveFile(f['id'])
				
				if f['version'] < dfile.version():
					self._download(dfile)
					f['version'] = dfile.version()
				else:
					print "File %s is up to date" % dfile.name()

			for d in entity['dependencies']:

				#TODO(Kirll): This is ugly. Also file download twice
				# Need additional check if file exist
				dfile = DriveFile(d['id'])
				
				if d['version'] < dfile.version():
					self._download(dfile)
					d['version'] = dfile.version()
				else:
					print "File %s is up to date" % dfile.name()

		self._sync_local_package()

if __name__ == '__main__':
	s = ShotPackage()
	s.sync()