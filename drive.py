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
    Find latest file that match the name
    '''
    files = service.files().list(q="title contains '%s'" % name).execute()['items'][0]
    return files

def upload_file(service, title, description, mime_type, parent_id, path):
  """Insert new file.

  Args:
    service: Drive API service instance.
    title: Title of the file to insert, including the extension.
    description: Description of the file to insert.
    parent_id: Parent folder's ID.
    mime_type: MIME type of the file to insert.
    path: Path of the file to insert.
  Returns:
    Inserted file metadata if successful, None otherwise.
  """

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

def upload_sequence(folder, parent):
    '''
    Upload files one by one in specifed folder
    '''
    files = os.listdir(folder)

    for f in files:
        root, name = folder, f

        upload_file(service=d,
                  title=name,
                  description='',
                  mime_type='',
                  parent_id=parent,
                  path=os.path.join(root, name))


d = get_instance()

if __name__ == '__main__':
    # cp_project_dir = get_file(d, 'CpProject')
    seq_dir = get_file(d, 'SQ05_SH16_01')
    upload_sequence('/Users/admin/Desktop/CurpigeonTest/img/SQ05_SH16', seq_dir['id'])
    # print cp_project_dir['id']
    # list_files(drive, 'TestProject')
    # print upload_file(service=d,
    #                   title='SQ05_SH16_5_KIR.nk',
    #                   description='This is a test upload',
    #                   mime_type='',
    #                   parent_id=cp_project_dir['id'],
    #                   path='/Users/admin/Desktop/CurpigeonTest/img/SQ05_SH16/SQ05_SQ16_0002.dpx')
