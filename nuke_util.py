import os
import simplejson
import nuke
import drive
from drive import d

reload(drive)

nuke_drive_location = {}

def nuke_meta():
    # Collect all external paths
    external_paths = []
    for node in nuke.allNodes('Read'):
        external_paths.append(node.knob('file').value())

    nuke_scene = nuke.root().knob('name').value()
    root, name = os.path.split(nuke_scene)

    # Cunstruct meta data object
    meta_data = {
            'name': name,
            'type': 'Nuke Script',
            'path': nuke_scene,
            'dependencies': external_paths
           }

    return meta_data

def publish():

    parent_id='0By7scHVmOMWFfmFUTUZlTkJ4MzNwUEZpNkJMalFGWVlJUm56bEVPdUpzWDFfSTN5VVlnVnc'
    meta_data = nuke_meta()
    service = d

    # Find if file with scene name already on Drive
    # If soo update file revision instead of creating a new one
    drive_file = drive.get_file(service, name=meta_data['name'],
                                         parent_id=parent_id)
    # If file already exist create his revision
    if drive_file:
        drive.update_file(service, file_id=drive_file['id'],
                                   path=meta_data['path'],
                                   new_revision=True)
    # Upload nuke file to drive
    else:
        drive.upload_file(service, path=meta_data['path'],
                                   parent_id=parent_id)




    # Upload sequences that use by this nuke file
    for path in meta_data['dependencies']:
        root, name = os.path.split(path)
        drive.upload_sequence(service, root, parent_id)

def embed_id(id):
    '''
        Save id to nuke root node as a string parameter
    '''
    r = nuke.root()
    k = nuke.String_Knob("drive_id", "Google Drive ID")
    r.addKnob(k)
