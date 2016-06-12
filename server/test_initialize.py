from unittest import TestCase
import rpi_db
import os

test_file = r'./blank.db'
original_file = None

class TestInitialize(TestCase):
    def test_initialize(self):
        global original_file
        self.addCleanup(self.shutdown)
        self.delete_test_file()
        original_file = rpi_db.dbfile
        rpi_db.dbfile = test_file
        rpi_db.initialize()
        devices = rpi_db.get_device_details()
        self.assertEquals(len(devices), 0)

    def delete_test_file(self):
        try:
            os.unlink(test_file)
        except FileNotFoundError:
            pass

    def shutdown(self):
        rpi_db.dbfile = original_file
        rpi_db.initialize()
        self.delete_test_file()
