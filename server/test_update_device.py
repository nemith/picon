from unittest import TestCase
import rpi_db


class TestUpdate_device(TestCase):
    def test_update_device(self):
        json = """
        {
            "hostname": "test-hostname",
            "sn": "testsn123",
            "interfaces": {
                "lo": {
                    "state": true,
                    "addrs": [ "127.0.0.1" ]
                },
                "eth0": {
                    "state": true,
                    "addrs": [ "192.0.2.1", "10.10.1.1", "2000:1:2:3::1" ]
                },
                "eth1": {
                    "state": false,
                    "addrs": [ "172.16.1.1" ]
                }
            },
            "ports": [
                "ttyUSB0",
                "ttyUSB1"
            ]
        }
        """
        rpi_db.update_device(json)
        dev_id = rpi_db.get_devid_by_sn('testsn123')
        dev_detail = rpi_db.get_device_details()
        rpi_db.delete_device_by_devid(dev_id)
        self.assertIsNotNone(dev_id)
