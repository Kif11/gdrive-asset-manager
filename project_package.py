import os
import sys
sys.path.insert(1, os.path.join(os.getcwd(), 'venv/Lib/site-packages'))
import json
from pathlib import Path
from drive import DriveFile
from drive import LocalFile

PACKAGE_PATH = os.getcwd()
PACKAGE_FILE_PATH = PACKAGE_PATH + '/project.json'
PROJECT_ID = '0By7scHVmOMWFX1N0X0RmRDh2UEk'

class ProjectPackage (object):
    def __init__(self):
        self.package = None
        self.project_path = Path(os.getcwd())
        self.project_json_file = self.project_path / Path('project.json')
        self.dproject_json = None

        # Initialize project directory
        self._init()

    def _init(self):
        # Create loacal project folder specified by user
        if not self.project_path.exists():
            self.project_path.mkdir()

        # Download package file from the gdrive
        if not self.project_json_file.exists():
            self.dproject_json = DriveFile(PROJECT_ID)
            project_dir = LocalFile(self.project_path)
            self.dproject_json.download(project_dir)
        else:
            print 'Using existing %s' % self.project_json_file

        self.package = self._read_package_file()

    def _read_package_file(self):
        """
        returns: JSON object
        """
        with open(str(self.project_json_file), 'r') as f:
            data = f.read()
        return json.loads(data)

    def _create_path(self, path):
        sub_path = os.path.dirname(path)
        if not os.path.exists(sub_path):
            self._create_path(sub_path)
        if not os.path.exists(path):
            os.mkdir(path)

    def _sync_local_package(self):
        with open(str(self.project_json_file), 'w') as f:
            json.dump(self.package, f, indent=4, sort_keys=True)

    def _sync_remote_package(self):
        self.dproject_json.update(LocalFile(self.project_json_file))

    def _download(self, f, dfile):
        dpath = dfile.get_path().relative_to('/My Drive/Bird Keeper/PostProd')
        fname = dfile.name()
        file_dir = self.project_path / dpath
        file_path = file_dir / fname

        if not file_dir.exists():
            self._create_path(str(file_dir))

        if file_path.exists():
            if f['version'] < dfile.version():
                print "Local file %s is older then remote version %s" % (f['name'], dfile.version())
                dfile.download(LocalFile(file_path))
                f['version'] = dfile.version()
            elif f['version'] > dfile.version():
                print 'Need to upload %s since locar version is higher then remote' % f['name']
            elif f['version'] == dfile.version():
                print "File %s is up to date" % dfile.name()
        else:
            print "Creating new local file %s of version %s" % (f['name'], dfile.version())
            dfile.download(LocalFile(file_path))
            f['version'] = dfile.version()

        self._sync_local_package()

    def add_entity(self, id):
        dfile = DriveFile(id)
        new_entity = {"name": str(dfile.name().name),
            "dependencies": [],
            "files": [
                {
                    "id": id,
                    "name": str(dfile.name()),
                    "version": 1
                }
        ]}

        self.package.append(new_entity)
        self._sync_local_package()
        self._sync_remote_package()

    def sync(self):
        """
        Sync all entity spicified in project.json from the gdrive to
        local project folder.
        """

        for entity in self.package:
            # Itarate trough all files
            for f in entity['files']:
                dfile = DriveFile(f['id'])
                self._download(f, dfile)
            # Iterate trought all dependencies
            for d in entity['dependencies']:
                dfile = DriveFile(d['id'])
                self._download(d, dfile)

if __name__ == '__main__':
    s = ProjectPackage()
    s.sync()
