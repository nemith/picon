from unittest import TestCase
import rpi_db


class TestInitialize(TestCase):
    def test_initialize(self):
        rpi_db.dbfile=r'./blank.db'
        rpi_db.initialize()
        devices = rpi_db.get_device_details()
        self.assertEquals(len(devices), 0)
