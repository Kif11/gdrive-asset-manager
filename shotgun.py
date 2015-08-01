from aau import sg
from pprint import pprint
from drive import get_instance
import drive
import os

class Project(object):

    def __init__(self, id=None):
        self.id = id

    def list_shots(self):
        fields = ['id', 'sg_sequence', 'code', 'sg_asset_type']

        filters = [
            ['project','is',{'type':'Project','id':self.id}],
            ]
        shots = sg.find("Shot", filters, fields)

        if len(shots) < 1:
            print "Couldn't find any shots"
            exit(0)
        else:
            print "Found " + str(len(shots)) + " shots"
            pprint (shots)

    def get_shot(self, code):

        fields = ['id', 'sg_sequence', 'code', 'sg_asset_type']

        filters = [
            ['project','is',{'type':'Project','id':self.id}],
            ['code', 'contains', code ]
            ]

        shot = sg.find("Shot", filters, fields)[0]

        return shot

    def list_versions(self, shot):
        fields = ['sg_uploaded_movie', 'id']

        filters = [
            ['project','is',{'type':'Project','id':self.id}],
            ['entity', 'is',{'type':'Shot', 'id': shot['id']}]
            ]
        versions = sg.find("Version", filters, fields)

        pprint(versions)

    def upload_nuke(self, shot, scene):

        result = sg.upload("Shot", shot['id'], scene,
                            field_name="sg_test_nuke_scene",
                            display_name="Test Nuke Scene")
        print result

    def publish(self, shot, path):

        service = get_instance()

        cp_project_dir = drive.get_file(service, 'CpProject')
        file_root, file_name = os.path.split(path)

        drive_file = drive.upload_file(service=service,
                          title=file_name,
                          description='This is a test upload',
                          mime_type='',
                          parent_id=cp_project_dir['id'],
                          path=path)

        data = {
            'project': {'type':'Project', 'id':self.id},
            'entity': {'type':'Shot', 'id': shot['id']},
            'code': file_name,
            'path_cache': drive_file['webContentLink'],
            'description': 'Test published file'
            }
        publishe = sg.create("PublishedFile", data)
        pprint(publishe)



curpigeon = Project(id=147)

# curpigeon.list_shots()
shot = curpigeon.get_shot('SQ05_SH16')
# print shot
# curpigeon.list_versions(shot)
# curpigeon.upload_nuke(shot, '/Users/admin/Desktop/SQ05_SH16_5_KIR.nk')
curpigeon.publish(shot, '/Users/admin/Desktop/SQ05_SH16_5_KIR.nk')
