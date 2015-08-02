import os
import simplejson
import nuke
import drive
from drive import d

reload(drive)
meta_file = os.path.join(nuke.script_directory(), '.dependencies')

def create_meta():
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

    # Write meta data to a file
    with open(meta_file, 'wb') as f:
        simplejson.dump(meta_data, f)

    return meta_data

def publish():

    # Reading meta data file
    with open(meta_file, 'rb') as f:
        meta_data = simplejson.load(f)

    meta_data = create_meta()
    service = d

    # TODO: Need to check file by id instead of name
    drive_file = drive.get_file(service, meta_data['name'])

    if drive_file:
        drive.update_file(service, drive_file['id'], meta_data['path'], new_revision=True)
    else:
        uploaded_file = drive.upload_file(service, meta_data['path'])

        meta_data['drive_id'] = uploaded_file['id']
        # Write meta data to a file
        with open(meta_file, 'wb') as f:
            simplejson.dump(meta_data, f)
