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

from pprint import pprint


SCOPES = 'https://www.googleapis.com/auth/drive.readonly'
CLIENT_SECRET_FILE = 'client_secrets.json'
APPLICATION_NAME = 'Drive API Quickstart'

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
    credential_path = os.path.join(credential_dir,
                                   'drive-quickstart.json')

    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        # flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatability with Python 2.6
            credentials = tools.run(flow, store)
        print 'Storing credentials to ' + credential_path
    return credentials

def drive():
    '''
    Returns:
        Authenticated instance of Google Drive API
    '''
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    drive = discovery.build('drive', 'v2', http=http)
    return drive

def get_path(drive, file):

    # import pdb; pdb.set_trace()

    parent = file['parents'][0]
    parent_file = drive.files().get(fileId=parent['id']).execute()
    title = parent_file['title']
    print title
    if title != 'My Drive':
        get_path(drive, parent_file)
    else:
        return 0


def main():

    d = drive()

    files = d.files().list(q="title contains 'SQ05_SH16_KIR.0001'").execute()['items']

    get_path(d, files[0])

    for file1 in files:

        file_id = file1['id']

        request = drive.files().get_media(fileId=file_id)
        fh = io.FileIO(file1['title'], mode='wb')
        media_request = apiclient.http.MediaIoBaseDownload(fh, request)

        while True:
            try:
              download_progress, done = media_request.next_chunk()
            except errors.HttpError, error:
              print 'An error occurred: %s' % error
              return
            if download_progress:
              print 'Download Progress: %d%%' % int(download_progress.progress() * 100)
            if done:
              print 'Download Complete'
              return

if __name__ == '__main__':
    main()
