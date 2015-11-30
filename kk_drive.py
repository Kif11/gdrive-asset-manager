from argparse import ArgumentParser
from drive import DriveFile


parser = ArgumentParser(description='Asset manager for Google Drive.')

parser.add_argument('-file', '-f', action="store",
                    metavar='drive_id',
                    help='')

parser.add_argument('-dependencies', '-d', action="store", nargs='*',
                    metavar='drive_ids',
                    help='')

args = parser.parse_args()

if args.file:
    drive_id = args.file
    print 'Drive ID: ', drive_id
    # dfile = DriveFile(drive_id)
    # dfile.add_dependencies()

if args.dependencies:
    print 'Dependencies:', args.dependencies
