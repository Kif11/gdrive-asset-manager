import os
import simplejson
import nuke
from pathlib import Path

import drive
reload(drive)
from drive import LocalFile, DriveFile, DriveUtils

class NukeLocalFile(object):
    def __init__(self):
        self.path = self._get_path()
        self.name = self.path.name
        self.nuke_scene = LocalFile(self.path)
        self.dependencies = self._get_dependencies()
        self.drive_id = None
        self.drive_file = None
        self.drive_scenes_location = '0By7scHVmOMWFflNFb3BXWWZFQmdwMmtpU3J0WE5nUmF6X2JqT2J0X3NYck1XZGlfWV8ybmc'
        self.drive_elements_location = '0By7scHVmOMWFfkdjUXFiX3JZZnNHcVFEUktZU0tSWk1kLXFiUmRNckEyMngwM0Z1cENFdWM'

    def _get_dependencies(self):
        # Collect all external paths
        external_paths = []
        for node in nuke.allNodes('Read'):
            external_paths.append(node.knob('file').value())
        return external_paths

    def _get_path(self):
        return Path(nuke.root().knob('name').value())

    def publish(self):

        drive_nuke = DriveUtils().get_file(self.name, parent_id=self.drive_scenes_location)

        if not drive_nuke:
            self.nuke_scene.upload(self.drive_scenes_location)
        else:
            print 'Update file here'

        # for f in self.dependencies:
        #     path = Path(f)
        #     folder = LocalFile(path.parent)
        #     folder.upload(self.drive_elements_location)


def embed_id(id):
    '''
        Save id to nuke root node as a string parameter
    '''
    r = nuke.root()
    k = nuke.String_Knob("drive_id", "Google Drive ID")
    r.addKnob(k)
