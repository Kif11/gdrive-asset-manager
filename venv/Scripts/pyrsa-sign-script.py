#!C:\Users\curpigeon\Desktop\kk_drive\venv\Scripts\python2.7.exe
# EASY-INSTALL-ENTRY-SCRIPT: 'rsa==3.2','console_scripts','pyrsa-sign'
__requires__ = 'rsa==3.2'
import sys
from pkg_resources import load_entry_point

if __name__ == '__main__':
    sys.exit(
        load_entry_point('rsa==3.2', 'console_scripts', 'pyrsa-sign')()
    )
