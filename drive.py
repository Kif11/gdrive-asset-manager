import httplib2
import urllib
import os
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

class DriveUtils(object):
    def __init__(self):
        self.service = DriveService().authenticate()

    def get_file(self, name, parent_id=None):
        '''
        Find latest file that match the name. Not looking in trashed
        '''

        if parent_id:
            files = self.service.files().list(q="title = '%s' and trashed = false and '%s' in parents" % (name, parent_id)).execute()['items']
        else:
            files = self.service.files().list(q="title = '%s' and trashed = false" % name).execute()['items']

        if files:
            if len(files) == 1:
                return files[0]
            else:
                print '%d files have "%s" name' % (len(files), name)
                return
        else:
            print 'Nothing found matching "%s"' % name
            return

class DriveFile(DriveService):
    def __init__(self, id):
        super(self.__class__, self).__init__()
        self.id = id
        self.file = self._file()

    def _file(self):
        return self.service.files().get(fileId=self.id).execute()

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

    def _download_folder(self, drive_file, local_file):

        files = self._list_files(drive_file)

        # TODO: Need to create folder for downloading files

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
            self.download_file(self.file, local_file)

    def get_path(self):

        '''
        Construct a path to a drive file recursively asking for file parent
        '''
        # def parent_title(service, file, path_items=[])
        parent = file['parents'][0]
        parent_file = service.files().get(fileId=parent['id']).execute()
        title = parent_file['title']

        path_items = []
        while title != 'My Drive':
            path_items.append(title)
            parent = parent_file['parents'][0]
            parent_file = service.files().get(fileId=parent['id']).execute()
            title = parent_file['title']

        path_items.reverse()
        # import pdb; pdb.set_trace()
        path = '/My Drive'
        for i in path_items:
            path += '/' + i
        return path

    def update_file(service, file_id, path, new_revision):
      '''
      Update an existing file's metadata and content.

      Args:
        service: Drive API service instance.
        file_id: ID of the file to update.
        path: Filename of the new content to upload.
        new_revision: Whether or not to create a new revision for this file.
      Returns:
        Updated file metadata if successful, None otherwise.
      '''

      root, name = os.path.split(path)

      try:
        # First retrieve the file from the API.
        file = service.files().get(fileId=file_id).execute()

        # File's new metadata.
        file['title'] = name

        # File's new content.
        media_body = MediaFileUpload(
            path, mimetype='', resumable=True)

        # Send the request to the API.
        updated_file = service.files().update(
            fileId=file_id,
            body=file,
            newRevision=new_revision,
            media_body=media_body).execute()
        return updated_file
      except errors.HttpError, error:
        print 'An error occurred: %s' % error
        return None

    def insert_property(service, file_id, key, value, visibility):
      """
      Insert new custom file property.

      """
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
        self.path = Path(path)

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
            self._upload_file(parent_id)

if __name__ == '__main__':
    drive_util = DriveUtils()
    cp_test_dir = drive_util.get_file('CpTestProject')
    seq_drive_file = drive_util.get_file('SQ04_SH14_06_RIS.0001.exr')


    my_drive_file = DriveFile(drive_util.get_file('test_seq')['id'])
    download_dir = LocalFile('C:/Users/curpigeon/Desktop/kk_drive')
    my_drive_file.download(download_dir)

    # test_file = LocalFile('C:/Users/curpigeon/Desktop/kk_drive/test_seq')
    # test_file.upload(cp_test_dir['id'])
