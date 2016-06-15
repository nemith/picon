import os
import sqlite3
import datetime
import ipaddress
import sys


LISTENER_PORT_BASE = 10000
DBFILE = r'./server.db'
TUNNEL_SERVER = 'hack003.netengcode.com'


class DB:
    """
    Database connectivity object for Picon.  Uses SQLite3 for storage.

    Attributes:
        dbfile:     Location of the database file
    """
    def __init__(self):
        self._conn = None
        self.dbfile = DBFILE
        self.listener_port_base = LISTENER_PORT_BASE
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
                holdtime int,
                tunnelport int UNIQUE);
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
        self._conn.commit()

    def update_device(self, dev_data):
        """
        Takes registration data transmitted by the Picon device and stores it
        in the database.
        :param dev_data: Data dictionary from the device, converted from JSON
            format
        :return: Returns tunnel port info as assigned by assign_tunnelport()
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
        tunnel = self.assign_tunnelport(dev_id)
        resp = {
            "status": "ok",
            "tunnel": tunnel
        }
        return resp

    #def	allocate_tunnelport(dev_id, highport,lowport):
    #    """
    #    Assigns a new TCP tunnel port to the specified existing device.
    #    :param dev_id: ID of target device
    #    :return: None
    #    """
    #    c = self._conn.cursor()
    #    now = datetime.datetime.utcnow()
    #    if dev_id is not None:
    #        c.execute("""
    #            UPDATE devices set tunnelport=(
    #                WITH RECURSIVE
    #                cnt(tunnelport) AS (
    #                SELECT 2220
    #                UNION ALL
    #            SELECT tunnelport+1 FROM cnt
    #            LIMIT 200
    #      ) SELECT tunnelport
    #        FROM cnt
    #        WHERE tunnelport
    #        NOT IN (SELECT
    #            tunnelport
    #            FROM devices
    #            WHERE tunnelport IS NOT NULL )
    #            LIMIT 1 )
    #            WHERE dev_id=6
    #        """, [dev_data['hostname'], dev_data['sn'], now,
    #              dev_data['holdtime'], dev_id])
    #        self._conn.commit()
    #    else:
    #        c.execute("""
    #        insert into devices (
    #            hostname
    #            , sn
    #            , first_seen
    #            , last_updated
    #            , holdtime
    #        )
    #        values (?, ?, ?, ?, ?);
    #        """, [dev_data['hostname'], dev_data['sn'], now, now,
    #              dev_data['holdtime']])
    #        self._conn.commit()

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
        self.delete_listener_port_by_devid(dev_id)
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

    def assign_tunnelport(self, dev_id):
        """
        Assigns a TCP listening port to a device for a reverse SSH tunnel.
        Args:
            dev_id: device requesting a port

        Returns: assigned port number
        """
        current_port = self.get_tunnelport_by_devid(dev_id)
        if current_port is not None:
            return {
                "tunnelserver": TUNNEL_SERVER,
                "tunnelport": current_port
            }
        c = self._conn.cursor()
        c.execute("BEGIN EXCLUSIVE TRANSACTION;")   # locks database while we are looking for a port
        assigned_port = 0
        last_port = self.get_last_tunnelport_from_db(c)
        if last_port is not None:
            assigned_port = last_port + 1
        else:
            assigned_port = LISTENER_PORT_BASE
        c.execute("""
        update devices set
            tunnelport=?
        WHERE dev_id=?;""", [assigned_port, dev_id])
        self._conn.commit()
        return {
            "tunnelserver": TUNNEL_SERVER,
            "tunnelport": assigned_port
        }

    def get_tunnelport_by_devid(self, dev_id):
        c = self._conn.cursor()
        c.execute("select tunnelport from devices where dev_id=?;", [dev_id])
        results = c.fetchall()
        if len(results) > 0:
            return results[0][0]
        return None

    def get_last_tunnelport_from_db(self, c=None):
        if c is None:
            c = self._conn.cursor()
        c.execute("select tunnelport from devices order by tunnelport desc limit 1;")
        results = c.fetchall()
        if len(results) > 0:
            return results[0][0]
        else:
            return None

    def delete_listener_port_by_devid(self, dev_id):
        """
        Removes a device's SSH tunnel port from devices table.
        :param dev_id: Device id to delete
        :return: None
        """
        c = self._conn.cursor()
        c.execute("""
        update devices set
            tunnelport=NULL
        WHERE dev_id=?;""", [dev_id])
        self._conn.commit()

    def close(self):
        """
        Close database file
        :return: None
        """
        self._conn.close()

