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

SCOPES = 'https://www.googleapis.com/auth/drive'
CLIENT_SECRET_FILE = 'client_secrets.json'
TOKEN_FILE = 'token.json'

# TODO{kirill}: Figure out what's going on here?
try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None


class DriveService(object):

    def __new__(cls):
        inst = object.__new__(cls)
        return inst

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
        credential_path = os.path.join(credential_dir, TOKEN_FILE)

        # Save token
        store = oauth2client.file.Storage(credential_path)
        credentials = store.get()

        # If faled to retrive token from file create a new one
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(os.path.join(credential_dir, CLIENT_SECRET_FILE), SCOPES)
            if flags:
                credentials = tools.run_flow(flow, store, flags)
            else: # Needed only for compatability with Python 2.6
                credentials = tools.run(flow, store)
            print 'Storing credentials to ' + credential_path

        return credentials

    def _authenticate(self):
        '''
        Returns:
            Authenticated instance of Google Drive API
        '''
        credentials = self._get_credentials()
        http = credentials.authorize(httplib2.Http())
        service = discovery.build('drive', 'v2', http=http)

        return service



def get_file(service, name, parent_id=None):
    '''
    Find latest file that match the name. Not looking in trashed
    '''

    if parent_id:
        files = service.files().list(q="title = '%s' and trashed = false and '%s' in parents" % (name, parent_id)).execute()['items']
    else:
        files = service.files().list(q="title = '%s' and trashed = false" % name).execute()['items']

    if files:
        if len(files) == 1:
            print files
            return files[0]
        else:
            print '%d files have "%s" name' % (len(files), name)
            return
    else:
        print 'Nothing found matching "%s"' % name
        return

def get_path(service, file):

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

def upload_file(service, path, parent_id=None):
  '''
  Insert new file.

  Args:
    service: Drive API service instance.
    title: Title of the file to insert, including the extension.
    description: Description of the file to insert.
    parent_id: Parent folder's ID.
    mime_type: MIME type of the file to insert.
    path: Path of the file to insert.
  Returns:
    Inserted file metadata if successful, None otherwise.
  '''
  root, name = os.path.split(path)

  media = MediaFileUpload(path, '', resumable=True)

  body = {
    'title': name
  }
  # Set the parent folder.
  if parent_id:
    body['parents'] = [{'id': parent_id}]
  try:
    request = service.files().insert(body=body, media_body=media)
    response = None
    # Print path to currently copied file
    print path
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

def upload_sequence(service, folder, parent_id):
    '''
    Upload files one by one in specifed folder
    '''
    folder_root, folder_name = os.path.split(folder)
    files = os.listdir(folder)

    # Create parent sequence directory
    body = {'title': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [{'id': parent_id}]}
    drive_sq_root = d.files().insert(body=body).execute()

    for f in files:
        root, name = folder, f

        upload_file(service=service,
                    path=os.path.join(root, name),
                    parent_id=drive_sq_root['id'])

def download_file(service, file, destination):
    drive_root = get_path(service, file)
    drive_path = os.path.join(drive_root, file['title'])
    local_path = os.path.join(destination, file['title'])

    request = service.files().get_media(fileId=file['id'])
    fh = io.FileIO(local_path, mode='wb')
    media_request = apiclient.http.MediaIoBaseDownload(fh, request)

    print 'Downloading %s to %s' % (drive_path, local_path)

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

def list_files(service, folder):
    files = d.files().list(
            q="'%s' in parents and trashed = false" % folder['id']
            ).execute()['items']
    return files

def download_sequence(service, folder, destination):

    files = list_files(service, folder)

    for f in files:
        download_file(service, f, destination)

    print 'All files are downloaded'
    return files

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

def upload_nuke(service, nuke_scene):

    nuke_scene_dir_id = '0By7scHVmOMWFfl9kTkdRbnFlTTd0UGpIeHNERmozaDVOZXpHckdUazZuQldCZEVKSzQ5SGc'
    seq_dir_id = '0By7scHVmOMWFfkV4bkQ4emdSMDhwQ0RZR01acXI1Y3Q2X2V0UHl0c0FEMjZTaC1kenlEaWM'

    nuke_root, nuke_name = os.path.split(nuke_scene)

    # Read nuke dependency file
    with open(os.path.join(nuke_root, '.dependencies'), 'rb') as f:
        dependencies = simplejson.load(f)

    # Upload thouse dependencies
    for path in dependencies:
        root, name = os.path.split(path)
        upload_sequence(service=service,
                        folder=root,
                        parent_id=seq_dir_id)


    # Upload the nuke file to drive
    upload_file(service=service,
                path=nuke_scene,
                title=nuke_name,
                parent_id=nuke_scene_dir_id)

    # Set nuke file properties to reflect this dependencies
    # insert_property(service, file_id, key, value, visibility)


if __name__ == '__main__':
    service = DriveService()
    print dir(service)
    # print service.files().list(q="title = 'CpTestProject'").execute()['items']
