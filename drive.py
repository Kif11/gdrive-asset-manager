import sys
import os

sys.path.insert(1, os.path.join(os.getcwd(), 'venv/Lib/site-packages'))

import httplib2
import urllib
import io

from apiclient import discovery
from apiclient import errors
import apiclient
import oauth2client
from oauth2client import client
from oauth2client import tools
from apiclient.http import MediaFileUpload

from pprint import pprint
from progressbar import ProgressBar
import simplejson
from pathlib import Path

class DriveService(object):
    def __init__(self):

        self.SCOPES = 'https://www.googleapis.com/auth/drive'
        self.CLIENT_SECRET_FILE = 'client_secrets.json'
        self.TOKEN_FILE = 'token.json'

        try:
            import argparse
            self.flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
        except ImportError:
            self.flags = None

        self.service = self.authenticate()

    def _get_credentials(self):
        '''
        Gets valid user credentials from storage.

        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.

        Returns:
            Credentials, the obtained credential.
        '''
        home_dir = os.path.expanduser('~')
        credential_dir = os.path.dirname(os.path.realpath(__file__))

        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)

        # Path to credentil file that store an user token
        credential_path = os.path.join(credential_dir, self.TOKEN_FILE)

        # Save token
        store = oauth2client.file.Storage(credential_path)
        credentials = store.get()

        # If faled to retrive token from file create a new one
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(os.path.join(credential_dir, self.CLIENT_SECRET_FILE), self.SCOPES)
            if self.flags:
                credentials = tools.run_flow(flow, store, self.flags)
            else: # Needed only for compatability with Python 2.6
                credentials = tools.run(flow, store)
            print 'Storing credentials to ' + credential_path

        return credentials

    def authenticate(self):
        '''
        Returns:
            Authenticated instance of Google Drive API
        '''
        credentials = self._get_credentials()
        http = credentials.authorize(httplib2.Http())
        service = discovery.build('drive', 'v2', http=http)

        return service

class DriveFile(DriveService):
    """
    Class define drive file and all actions associated with it.
    """

    def __init__(self, id):
        super(self.__class__, self).__init__()
        self.id = id
        self.file = self._file()

    def _file(self):
        return self.service.files().get(fileId=self.id).execute()

    def _parent(self, drive_file):
        parent_id = drive_file['parents'][0]['id']
        parent = self.service.files().get(fileId=parent_id).execute()
        return parent

    def _list_files(self, drive_file):
        files = self.service.files().list(
                q="'%s' in parents and trashed = false" % drive_file['id']
                ).execute()['items']
        return files

    def _download_file(self, drive_file, local_file):
        local_path = local_file.path / Path(drive_file['title'])
        request = self.service.files().get_media(fileId=drive_file['id'])
        fh = io.FileIO(str(local_path), mode='wb')
        media_request = apiclient.http.MediaIoBaseDownload(fh, request)

        print 'Downloading %s' % local_path

        pbar = ProgressBar(maxval=100).start()
        while True:
            try:
              download_progress, done = media_request.next_chunk()
            except errors.HttpError, error:
              print 'An error occurred: %s' % error
              return
            if download_progress:
                pbar.update(int(download_progress.progress() * 100))
            if done:
              print 'Download Complete'
              return

    def file_in_folder(self, name, parent_id):
        """
        Find a file in specified directory that match the name. Thresh folder is skiped.
        """
        files = self.service.files().list(q="title = '%s' and trashed = false and '%s' in parents"
                                            % (name, parent_id)).execute()['items']

        if files:
            if len(files) == 1:
                return files[0]
            else:
                print '%d files have "%s" name' % (len(files), name)
                return
        else:
            print 'Nothing found matching "%s"' % name
            return

    def _download_folder(self, drive_file, local_file):

        files = self._list_files(drive_file)
        print "PATH", local_file.path
        local_file.path = local_file.path / Path(drive_file['title'])
        if not local_file.path.exists():
            local_file.path.mkdir()

        for f in files:
            print f['title']
            self._download_file(f, local_file)

        print 'All files are downloaded'
        return files

    def download(self, local_file):

        folder_type = 'application/vnd.google-apps.folder'

        if self.file['mimeType'] == folder_type:
            self._download_folder(self.file, local_file)
        else:
            self._download_file(self.file, local_file)

    def get_path(self):

        '''
        Construct a path to a drive file recursively asking for file parent
        '''
        # def parent_title(service, file, path_items=[])
        parent = self.file['parents'][0]
        parent_file = self.service.files().get(fileId=parent['id']).execute()
        title = parent_file['title']

        path_items = []
        while title != 'My Drive':
            path_items.append(title)
            parent = parent_file['parents'][0]
            parent_file = self.service.files().get(fileId=parent['id']).execute()
            title = parent_file['title']

        path_items.reverse()
        # import pdb; pdb.set_trace()
        path = '/My Drive'
        for i in path_items:
            path += '/' + i
        return Path(path)

    def update(self, local_file):
        """
        Update an existing file's metadata and content.

        Returns:
        Updated file metadata if successful, None otherwise.
        """
        # try:
        # First retrieve the file from the API.
        dfile = self.service.files().get(fileId=self.id).execute()

        # File's new metadata.
        dfile['title'] = str(local_file.path.name)

        # File's new content.
        media_body = MediaFileUpload(
            str(local_file.path), mimetype='', resumable=True)

        try:
          request = self.service.files().update(fileId=self.id,
                                                body=dfile,
                                                newRevision=True,
                                                media_body=media_body)
          response = None
          # Create a progress bar object
          pbar = ProgressBar(maxval=100).start()
          while response is None:
            status, response = request.next_chunk()
            if status:
              # Update progress bar
              pbar.update(int(status.progress() * 100))
          print "Upload Complete!"
          return request.execute()
        except errors.HttpError, error:
          print 'An error occured: %s' % error
          return None


    #     # Send the request to the API.
    #     updated_file = self.service.files().update(
    #         fileId=self.id,
    #         body=dfile,
    #         newRevision=True,
    #         media_body=media_body).execute()
    #     print 'File updated successfuly!'
    #     return updated_file
    #   except errors.HttpError, error:
    #     print 'An error occurred: %s' % error
    #     return None

    def add_property(self, drive_file, key, value):
      """
      Insert new custom file property.

      """
      visibility = 'PUBLIC'
      body = {
        'key': key,
        'value': value,
        'visibility': visibility
      }

      try:
        p = service.properties().insert(
            fileId=file_id, body=body).execute()
        return p
      except errors.HttpError, error:
        print 'An error occurred: %s' % error
      return None

class LocalFile(DriveService):
    def __init__(self, path):
        super(self.__class__, self).__init__()

        if isinstance(path, str):
            self.path = Path(path)
        else:
            self.path = path

    def _upload_file(self, path, parent_id):

        media = MediaFileUpload(str(path), '', resumable=True)
        body = {
          'title': path.name
        }
        # Set the parent folder.
        if parent_id:
          body['parents'] = [{'id': parent_id}]
        try:
          request = self.service.files().insert(body=body, media_body=media)
          response = None
          # Create a progress bar object
          pbar = ProgressBar(maxval=100).start()
          while response is None:
            status, response = request.next_chunk()
            if status:
              # Update progress bar
              pbar.update(int(status.progress() * 100))
          print "Upload Complete!"
          return request.execute()
        except errors.HttpError, error:
          print 'An error occured: %s' % error
          return None

    def _upload_folder(self, parent_id):
        '''
        Upload files one by one in specifed folder
        '''
        # Create parent sequence directory
        body = {'title': self.path.name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [{'id': parent_id}]}
        parent = self.service.files().insert(body=body).execute()

        for f in self.path.iterdir():
            self._upload_file(f, parent['id'])

    def upload(self, parent_id):
        # Check if file is a folder
        if self.path.is_dir():
            self._upload_folder(parent_id)
        else:
            self._upload_file(self.path, parent_id)

class File(object):
    def __init__(self, drive_file, local_file):
        self.drive_file = drive_file
        self.local_file = local_file

    def upload(self):
        print 'Upload file here'

if __name__ == '__main__':
    my_drive_file = DriveFile('0B9yAgxKfBUjWaTVVbDlRcnFHN28')
    print(my_drive_file.get_path())
    # download_dir = LocalFile('C:/Users/kkirill2/Desktop')
    # my_drive_file.download(download_dir)


    # local_file = LocalFile('G:/Code/kk_drive/Project/Scene/SQ05/SH16/nuke/SQ05_Sh16_01.nk')
    # drive_file = DriveFile('My Drive/CpTestProject/shots/SQ05_SH16/scenes/nuke/SQ05_Sh16_01.nk')


    # drive_util = DriveUtils()
    # seq_drive_file = drive_util.get_file('SQ04_SH14_06_RIS.0001.exr')
    #
    #
    # my_drive_file = DriveFile(drive_util.get_file('CpTestProject')['id'])
    # download_dir = LocalFile('')
    # my_drive_file.download(download_dir)

#     assets = [

#     {"name":"paperBird",
#         "tasks": [{
#             "name": "rig",
#             "driveFiles": [{
#                         "name": "TBK_Rig_PaperBird_test.ma",
#                         "id": "0By7scHVmOMWFYnpyd2VyakxzUm8",
#                         "type": "maya"
#                           }]
#             },
#             {"name": "texture",
#             "driveFiles": []
#             }]
#         }]

#     shots = [
#     {
#         "sequence": 1,
#         "code": "SQ01_SH010",
#         "tasks": {
#             "anim": {
#             },
#             "render": {
#             }
#         }
#     },
#     {
#         "sequence": 1,
#         "code": "SQ01_SH011",
#         "tasks": {}
#     }
# ]

    # test_file = LocalFile('/Users/amy/Desktop/kk_drive/SQ02_SH010_testFile.ma')
    # test_file.upload('0By7scHVmOMWFLVVIenVoUVhCWnM')
    # drive_file = DriveFile('0By7scHVmOMWFcVQ3bTlHNGZkWFk')
    # drive_file.update(test_file)

    # for asset in assets:
    #     print 'Name: ', asset['name']
    #     for task in asset['tasks']:
    #         print 'Task: ', task['name']
    #         for f in task['driveFiles']:
    #             print 'File: ', f['name']
    #             print 'FileId: ', f['id']

