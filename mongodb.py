import sys
import os
sys.path.insert(1, os.path.join(os.getcwd(), 'venv/Lib/site-packages'))
import pymongo
from bson.objectid import ObjectId

class MongoFile(object):

    def __init__(self, mfile_id=None):
        MONGODB_URI = 'mongodb://kif11:Natoma250@ds039484.mongolab.com:39484/pubdb'
        client = pymongo.MongoClient(MONGODB_URI)
        self.db = client.get_default_database()
        self.files = self.db['files']
        self.mfile_id = ObjectId(mfile_id)
        if mfile_id is not None:
            self.data = self._data()

    def _data(self):
        return self.files.find_one({'_id':self.mfile_id})

    def new(self, data):
        """
        returns: Mongo ObjectId.
        """
        return str(self.files.insert(data))

    def update(self):
        """
        Update remote database with self.data.
        """
        print 'Updating with data', self.data
        self.files.update_one({'_id':self.mfile_id}, {'$set': self.data})

if __name__ == '__main__':
    mfile = MongoFile('565b8895893e39d95712001f')
    mfile.data['dependencies'].pop(0)
    mfile.update()
