from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

gauth = GoogleAuth()
gauth.LocalWebserverAuth()

drive = GoogleDrive(gauth)

# Auto-iterate through all files that matches this query
file_list = drive.ListFile({'q': "title contains 'SQ05_SH16'"}).GetList()

for file1 in file_list:
    # print 'title: %s, id: %s' % (file1['title'], file1['id'])
    # file1.GetContentFile(file1['title'])

    print dir(file1)

    # for key, value in file1.items():
    #     print key, ':', value
