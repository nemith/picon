import os
import sqlite3
import datetime
import ipaddress
import sys


class DB:
    """
    Database connectivity object for Picon.  Uses SQLite3 for storage.

    Attributes:
        dbfile:     Location of the database file
    """
    def __init__(self):
        self._conn = None
        self.dbfile = r'./server.db'
        self.listener_port_base = 5000
        self.initialize()

    def initialize(self):
        """
        Initialize the database connection.  If the database file does not
        exist, create it and initialize the schema.
        :return: None
        """
        dbfile_exists = os.path.isfile(self.dbfile)
        self._conn = sqlite3.connect(self.dbfile)
        if dbfile_exists:
            if not self.is_schema_installed():
                raise Exception("server.db does not have schema configured")
        else:
            self.create_schema()

    def is_schema_installed(self):
        """
        Returns true if tables are found in the database file, false if not.
        :return: None
        """
        c = self._conn.cursor()
        c.execute("""
            select name from sqlite_master where type='table';
        """)
        return len(c.fetchall()) > 0

    def create_schema(self):
        """
        Creates database schema in a blank database.
        :return: None
        """
        c = self._conn.cursor()
        c.execute("""
            create table devices (
                dev_id integer primary key,
                hostname text,
                sn text,
                first_seen datetime,
                last_updated datetime,
                holdtime int);
        """)
        c.execute("create table serialports (dev_id integer, port_name text);")
        c.execute("""
            create table interfaces (
                dev_id integer,
                int_name text,
                state integer,
                addr text,
                ip_version integer);
        """)
        c.execute("""
            create table listener_ports (
                port_num integer primary key,
                dev_id integer,
                first_assigned datetime,
                last_active datetime);
        """)
        self._conn.commit()

    def update_device(self, dev_data):
        """
        Takes registration data transmitted by the Picon device and stores it
        in the database.
        :param dev_data: Data dictionary from the device, converted from JSON
            format
        :return: None
        """
        dev_id = self.get_devid_by_sn(dev_data['sn'])
        c = self._conn.cursor()
        now = datetime.datetime.utcnow()
        if dev_id is not None:
            c.execute("""
            update devices set
                hostname=?
                , sn=?
                , last_updated=?
                , holdtime=?
            where dev_id=?;
            """, [dev_data['hostname'], dev_data['sn'], now,
                  dev_data['holdtime'], dev_id])
            self._conn.commit()
        else:
            c.execute("""
            insert into devices (
                hostname
                , sn
                , first_seen
                , last_updated
                , holdtime
            )
            values (?, ?, ?, ?, ?);
            """, [dev_data['hostname'], dev_data['sn'], now, now,
                  dev_data['holdtime']])
            self._conn.commit()
        dev_id = self.get_devid_by_sn(dev_data['sn'])
        self.update_interfaces(dev_id, dev_data['interfaces'])
        self.update_serialports(dev_id, dev_data['ports'])

    def get_interface_details(self, dev_id):
        """
        Get interface details for a particular device.
        :param dev_id: dev_id of the device
        :return: dict() containing items keyed by interface name
        """
        c = self._conn.cursor()
        c.execute("""select int_name, state, addr, ip_version from
                  interfaces where dev_id=?""", [dev_id])
        results = c.fetchall()
        if_list = dict()
        for r in results:
            if r[0] not in if_list:
                if_list[r[0]] = {
                    'addrs': [],
                    'state': r[1]
                }
            if_list[r[0]]['addrs'].append(r[2])
        return if_list

    def get_serialport_details(self, dev_id):
        """
        Get available serial port details for a particular device.
        :param dev_id: dev_id of the device
        :return: list of serial port device names ("ttyUSB0, ttyUSB1")
        """
        c = self._conn.cursor()
        c.execute("select port_name from serialports where dev_id=?", [dev_id])
        results = c.fetchall()
        return [r[0] for r in results]

    def get_device_details(self, dev_id=None):
        """
        Get all available details for a particular device, or from all devices
        if a device id is not provided.
        :param dev_id: ID of a particular device, or None to return all devices
        :return: List of dicts() describing all devices
        """
        devlist = list()
        c = self._conn.cursor()
        if dev_id is None:
            c.execute('select dev_id, hostname, sn, first_seen, last_updated, '
                      'holdtime from devices;')
        else:
            c.execute('select dev_id, hostname, sn, first_seen, last_updated, '
                      'holdtime from devices where dev_id=?', [dev_id])
        results = c.fetchall()
        for r in results:
            dev_dict = dict()
            dev_id = r[0]
            dev_dict['dev_id'] = r[0]
            dev_dict['hostname'] = r[1]
            dev_dict['sn'] = r[2]
            dev_dict['first_seen'] = r[3]
            dev_dict['last_updated'] = r[4]
            dev_dict['holdtime'] = r[5]
            dev_dict['interfaces'] = self.get_interface_details(dev_id)
            dev_dict['ports'] = self.get_serialport_details(dev_id)
            devlist.append(dev_dict)
        return devlist

    def get_devid_by_sn(self, sn):
        """
        Obtain a device id given a device serial number.
        :param sn: string containing the serial number
        :return: device ID if found, None otherwise
        """
        c = self._conn.cursor()
        c.execute("""
            select
                dev_id
            from devices
            where sn=?;
        """, [sn])
        results = c.fetchall()
        if len(results) > 0:
            return results[0][0]
        return None

    def update_interfaces(self, dev_id, iflist):
        """
        Adds interfaces to the database for a particular device.
        :param dev_id: Device ID of the unit
        :param iflist: Data dict() describing the interfaces
        :return: None
        """
        self.delete_interfaces_by_devid(dev_id)
        ifstates = [(dev_id, ifname, iflist[ifname]['state'])
                    for ifname in iflist]
        insert_list = list()
        for i in ifstates:
            insert_list.extend([(i[0], i[1], i[2], addr,
                                 self.ip_version(addr))
                                for addr in iflist[i[1]]['addrs']])
        c = self._conn.cursor()
        c.executemany("""
        insert into interfaces (
            dev_id
            , int_name
            , state
            , addr
            , ip_version
        )
        values (?, ?, ?, ?, ?);
            """, insert_list)
        self._conn.commit()

    def delete_device_by_devid(self, dev_id):
        """
        Deletes a device from all tables.
        :param dev_id: Device id to delete
        :return: None
        """
        self.delete_interfaces_by_devid(dev_id)
        self.delete_serialports_by_devid(dev_id)
        c = self._conn.cursor()
        c.execute("delete from devices where dev_id=?;", [dev_id])
        self._conn.commit()

    def delete_interfaces_by_devid(self, dev_id):
        """
        Deletes a device's interfaces from interface table.
        :param dev_id: Device id to delete
        :return: None
        """
        c = self._conn.cursor()
        c.execute("""
        delete from interfaces where dev_id=?;
        """, [dev_id])
        self._conn.commit()

    def update_serialports(self, dev_id, portlist):
        """
        Add serial ports to the database.
        :param dev_id: Device id of the owning device
        :param portlist: List of str()'s describing the port names
        :return: None
        """
        self.delete_serialports_by_devid(dev_id)
        c = self._conn.cursor()
        insert_list = [(dev_id, p) for p in portlist]
        c.executemany("""
        insert into serialports (
            dev_id
            , port_name
        )
        values (?, ?);""", insert_list)
        self._conn.commit()

    def delete_serialports_by_devid(self, dev_id):
        """
        Deletes a device's serial ports from serialports table.
        :param dev_id: Device id to delete
        :return: None
        """
        c = self._conn.cursor()
        c.execute("""
        delete from serialports where dev_id=?;
        """, [dev_id])
        self._conn.commit()

    @staticmethod
    def ip_version(addr):
        """
        Given an IPvX address, solves for X
        :param addr: IP address as str()
        :return: 4 if IPv4, 6 if IPv6
        """
        i = None
        try:
            i = ipaddress.ip_address(addr)
        except ipaddress.AddressValueError:
            return None
        if type(i) is ipaddress.IPv4Address:
            return 4
        if type(i) is ipaddress.IPv6Address:
            return 6
        return None

    def assign_listener_port(self, dev_id):
        """
        Assigns a TCP listening port to a device for a reverse SSH tunnel.
        Args:
            dev_id: device requesting a port

        Returns: assigned port number
        """
        port = get_listener_port_by_devid(dev_id)
        if port is not None:
            return port
        used_ports = set()
        used_ports |= get_listener_ports_from_db();
        used_ports |= get_listener_ports_from_netstat();
        i = self.listener_port_base
        while i not in used_ports() and i < 65536:
            i += 1
            if i == 65536:
                return None
        now = datetime.datetime.utcnow()
        c = self._conn.cursor()
        c.execute("""
        insert into listener_ports (
            port_num
            , dev_id
            , first_assigned
            , last_active
        )
        values (?, ?, ?, ?, ?);
        """, [i, dev_id, now, now])
        self._conn.commit()
        return i

    def get_listener_port_by_devid(self, dev_id):
        c = self._conn.cursor()
        c.execute("select port_num from listener_ports where dev_id=?", [dev_id])
        results = c.fetchall()
        if len(results) > 0:
            return results[0][0]
        return None

    def get_listener_ports_from_db(self):
        c = self._conn.cursor()
        c.execute("select port_num from listener_ports")
        results = c.fetchall()
        return {r[0] for r in results}

    def get_listener_ports_from_netstat(self):
        # TODO: implement netstat reader for linux
        return set()

    def close(self):
        """
        Close database file
        :return: None
        """
        self._conn.close()

