from unittest import TestCase
import picon_db
import os

test_file = r'./blank.db'
original_file = None

class TestInitialize(TestCase):
    def test_initialize(self):
        db = picon_db.PiconDB()
        global original_file
        self.addCleanup(self.shutdown, db)
        self.delete_test_file()
        original_file = db.dbfile
        db.dbfile = test_file
        db.initialize()
        devices = db.get_device_details()
        self.assertEquals(len(devices), 0)

    def delete_test_file(self):
        try:
            os.unlink(test_file)
        except FileNotFoundError:
            pass

    def shutdown(self, db):
        db.dbfile = original_file
        db.initialize()
        db.close()
        self.delete_test_file()
