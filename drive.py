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
APPLICATION_NAME = 'Drive API Quickstart'

# TODO{kirill}: Fiure out what's going on here?
try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

def get_credentials():
    '''
    Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    '''
    home_dir = os.path.expanduser('~')
    credential_dir = os.getcwd()
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)

    # Path to credentil file that store an user token
    credential_path = os.path.join(credential_dir,
                                   'token.json')
    # Save token
    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    # If faled to retrive token from file create a new one
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        # flow.user_agent = APPLICATION_NAME # Why do we need application name?
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatability with Python 2.6
            credentials = tools.run(flow, store)
        print 'Storing credentials to ' + credential_path
    return credentials

def get_instance():
    '''
    Returns:
        Authenticated instance of Google Drive API
    '''
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    drive = discovery.build('drive', 'v2', http=http)
    return drive

def get_file(service, name):
    '''
    Find latest file that match the name. Not looking in trashed
    '''
    files = service.files().list(q="title = '%s' and trashed = false" % name).execute()['items']
    if len(files) == 1:
        return files[0]
    else:
        print '%d files have "%s" name' % (len(files), name)
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

def upload_file(service, title, parent_id, path, description='', mime_type=''):
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

  media = MediaFileUpload(path, mime_type, resumable=True)

  body = {
    'title': title,
    'description': description,
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
        # print "Uploaded %d%%." % int(status.progress() * 100)
        # Update progress bar
        # TODO(kirill): Check if this progress bar works on Windows
        pbar.update(int(status.progress() * 100))
    print "Upload Complete!"
    return file
  except errors.HttpError, error:
    print 'An error occured: %s' % error
    return None

def upload_sequence(service, folder, parent_id):
    '''
    Upload files one by one in specifed folder
    '''
    files = os.listdir(folder)

    for f in files:
        root, name = folder, f

        upload_file(service=service,
                  title=name,
                  description='',
                  mime_type='',
                  parent_id=parent_id,
                  path=os.path.join(root, name))

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

def file_from_path(service, path):

    root, name = os.path.split(path)

    print root, name

    files = service.files().list(q="title contains '%s'" % name).execute()['items']

    for f in files:
        print f['title']
        if path == get_path(service, f):
            print 'Find match'

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

d = get_instance()

if __name__ == '__main__':

    # upload_nuke(d, '/Users/admin/Desktop/CurpigeonTest/SQ05_SH16_01_KIR.nk')

    nuke_file = get_file(d, 'TestRevision.nk')

    update_file(service=d,
                file_id=nuke_file['id'],
                path='/Users/admin/Desktop/CurpigeonTest/TestRevision.nk',
                new_revision=True)

    # d.files().list(q="title='nuke and childrens has '")

    # file_from_path(d, '/My Drive/CpProject/Scenes/SQ05/SH16/maya')

    # cp_project_dir = get_file(d, 'CpProject')
    # seq_dir = get_file(d, 'SQ05_SH16_01')
    # single_dpx = get_file(d, 'SQ05_SQ16_0001.dpx')
    #
    # insert_property(d, seq_dir['id'], 'linked_file_id', single_dpx['id'], 'PUBLIC')
    # download_sequence(d, seq_dir, '/Users/admin/Desktop/SQ')

    # download_file(d, single_dpx, '/Users/admin/Desktop/')
    # print get_path(d, seq_dir)

    # seq_dir = get_file(d, 'SQ05_SH16_01')
    # upload_sequence('/Users/admin/Desktop/CurpigeonTest/img/SQ05_SH16', seq_dir['id'])
    # print cp_project_dir['id']
    # list_files(drive, 'TestProject')
    # print upload_file(service=d,
    #                   title='SQ05_SH16_5_KIR.nk',
    #                   description='This is a test upload',
    #                   mime_type='',
    #                   parent_id=cp_project_dir['id'],
    #                   path='/Users/admin/Desktop/CurpigeonTest/img/SQ05_SH16/SQ05_SQ16_0002.dpx')
