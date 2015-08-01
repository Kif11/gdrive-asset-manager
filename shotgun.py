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

    def publish(self, drive_file, sg_shot, version=1, user_id=1201, type_id=8):
        '''
        type_id: 8 - Nuke Script, 9 - Rendered Image
        '''

        data = {
            'project': {'type':'Project', 'id':self.id},
            'entity': {'type':'Shot', 'id': sg_shot['id']},
            'code': drive_file['title'],
            'path_cache': drive_file['alternateLink'],
            'sg_drive_id': drive_file['id'],
            'version_number': version,
            'published_file_type': {'type':'PublishedFileType', 'id':type_id},
            'description': 'Test published file',
            'created_by': {'type':'HumanUser','id':user_id},
            }

        publish = sg.create("PublishedFile", data)
        pprint(publish)


curpigeon = Project(id=147)
d = drive.get_instance()

drive_seq_dir = drive.get_file(d, 'SQ05_SH16_01')
sg_shot = curpigeon.get_shot('SQ05_SH16')

# pprint(drive_seq_dir)
# print shot
# curpigeon.list_versions(shot)
# curpigeon.upload_nuke(shot, '/Users/admin/Desktop/SQ05_SH16_5_KIR.nk')
curpigeon.publish(drive_file=drive_seq_dir, sg_shot=sg_shot, version=2,  type_id=9)
