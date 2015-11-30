PROJECT_PATH = '/User/amy/Desktop/TestProject'
PACKAGE_PATH = os.getcwd()
PACKAGE_FILE_PATH = PACKAGE_PATH + '/project.json'
PROJECT_ID = '0By7scHVmOMWFX1N0X0RmRDh2UEk'

class Project(object):
    def __init__(self):
        self.path
        self.id
        self.package_file = self.path / Path('project.json')

    def initilize(self):
        """
        Create local folder and package file inside.
        """
        if not self.project_path.exists():
            self.project_path.mkdir()

    def _download_package

class Package(object):

    def __init__(self):
        self.id
        self.project_path = PROJECT_PATH
        self.package_file = self.project_path / Path('project.json')

    def _download(self):
        # Download package file from the gdrive
        if not self.package_file.exists():
            self.dproject_json = DriveFile(self.id)
            project_dir = LocalFile(self.package_file)
            self.dproject_json.download(project_dir)
        else:
            print 'Using existing %s' % self.package_file

    def _read_file(self):
        """
        returns: Return context of project.json as JSON object.
        """
        with open(str(self.project_json_file), 'r') as f:
            data = f.read()
        return json.loads(data)


class Shot(object):
    def __init__(self, code):
        self.project = Project()
        self.code = code
