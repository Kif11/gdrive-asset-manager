import os
import sys
sys.path.insert(1, os.path.join(os.getcwd(), 'venv/Lib/site-packages'))
import json
from pathlib import Path
from drive import DriveFile
from drive import LocalFile

PACKAGE_PATH = os.getcwd()
PACKAGE_FILE_PATH = PACKAGE_PATH + '/project.json'
PROJECT_DIR = Path('/Users/amy/Desctop/BirdKeeperTest')


class ProjectPackage (object):
    def __init__(self):
        self.package = self._read_package_file()

    def _init(self):
        # Create loacal project folder specified by user
        # Download package file from the gdrive

        # TODO(Kirill): Create command line interface with the following features:
        # init, sync, versionup, sync item etc...

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

    def _download(self, f, dfile):

        dpath = dfile.get_path().relative_to('/My Drive/Bird Keeper/PostProd')
        fname = dfile.name()
        file_dir = PROJECT_DIR / dpath
        file_path = file_dir / fname

        if not file_dir.exists():
            self._create_path(str(file_dir))

        if file_path.exists():
            if f['version'] < dfile.version():
                dfile.download(LocalFile(file_path))
                f['version'] = dfile.version()
            elif f['version'] > dfile.version():
                print 'Need to upload %s since locar version is higher then remote' % f['name']
            elif f['version'] == dfile.version():
                print "File %s is up to date" % dfile.name()
        else:
            dfile.download(LocalFile(file_path))

    def sync(self):

        for entity in self.package:
            # Itarate trough all files
            for f in entity['files']:
                dfile = DriveFile(f['id'])
                self._download(f, dfile)
            # Iterate trought all dependencies
            for d in entity['dependencies']:
                dfile = DriveFile(d['id'])
                self._download(d, dfile)

        self._sync_local_package()

if __name__ == '__main__':
    s = ProjectPackage()
    s.sync()
