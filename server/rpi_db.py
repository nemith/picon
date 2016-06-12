#!/usr/bin/python
#
# rpi_db.py
#
# Library for integrating with SQLite3


import sqlite3
import datetime
import ipaddress


_conn = sqlite3.connect('./server.db')


def is_schema_installed():
    c = _conn.cursor()
    c.execute("""
        select name from sqlite_master where type='table';
    """)
    return len(c.fetchall()) > 0

def create_schema():
    c = _conn.cursor()
    c.execute("""
        create table devices (
            dev_id integer primary key,
            hostname text,
            sn text,
            first_seen datetime,
            last_updated datetime);
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
    _conn.commit()


def update_device(dev_data):
    dev_id = get_devid_by_sn(dev_data['sn'])
    c = _conn.cursor()
    now = datetime.datetime.now()
    if dev_id is not None:
        c.execute("""
        update devices set
            hostname=?
            , sn=?
            , last_updated=?
        where dev_id=?;
        """, [dev_data['hostname'], dev_data['sn'], now, dev_id])
        _conn.commit()
    else:
        c.execute("""
        insert into devices (
            hostname
            , sn
            , first_seen
            , last_updated
        )
        values (?, ?, ?, ?);
        """, [dev_data['hostname'], dev_data['sn'], now, now])
        _conn.commit()
    dev_id = get_devid_by_sn(dev_data['sn'])
    update_interfaces(dev_id, dev_data['interfaces'])
    update_serialports(dev_id, dev_data['ports'])


def get_interface_details(dev_id):
    c = _conn.cursor()
    c.execute("select int_name, state, addr, ip_version from interfaces where dev_id=?", [dev_id])
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


def get_serialport_details(dev_id):
    c = _conn.cursor()
    c.execute("select port_name from serialports where dev_id=?", [dev_id])
    results = c.fetchall()
    return [r[0] for r in results]


def get_device_details(dev_id=None):
    devlist = list()
    c = _conn.cursor()
    if dev_id is None:
        c.execute('select dev_id, hostname, sn, first_seen, last_updated from devices;')
    else:
        c.execute('select dev_id, hostname, sn, first_seen, last_updated from devices where dev_id=?', [dev_id])
    results = c.fetchall()
    for r in results:
        dev_dict = dict()
        dev_id = r[0]
        dev_dict['dev_id'] = r[0]
        dev_dict['hostname'] = r[1]
        dev_dict['sn'] = r[2]
        dev_dict['first_seen'] = r[3]
        dev_dict['last_updated'] = r[4]
        dev_dict['interfaces'] = get_interface_details(dev_id)
        dev_dict['ports'] = get_serialport_details(dev_id)
        devlist.append(dev_dict)
    return devlist


def get_devid_by_sn(sn):
    c = _conn.cursor()
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

def update_interfaces(dev_id, iflist):
    delete_interfaces_by_devid(dev_id)
    ifstates = [(dev_id, ifname, iflist[ifname]['state']) for ifname in iflist]
    insert_list = list()
    for i in ifstates:
        insert_list.extend([(i[0], i[1], i[2], addr, ip_version(addr)) for addr in iflist[i[1]]['addrs']])
    c = _conn.cursor()
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
    _conn.commit()


def delete_device_by_devid(dev_id):
    delete_interfaces_by_devid(dev_id)
    delete_serialports_by_devid(dev_id)
    c = _conn.cursor()
    c.execute("delete from devices where dev_id=?;", [dev_id])
    _conn.commit()


def delete_interfaces_by_devid(dev_id):
    c = _conn.cursor()
    c.execute("""
    delete from interfaces where dev_id=?;
    """, [dev_id])
    _conn.commit()


def update_serialports(dev_id, portlist):
    delete_serialports_by_devid(dev_id)
    c = _conn.cursor()
    insert_list = [(dev_id, p) for p in portlist]
    c.executemany("""
    insert into serialports (
        dev_id
        , port_name
    )
    values (?, ?);""", insert_list)
    _conn.commit()


def delete_serialports_by_devid(dev_id):
    c = _conn.cursor()
    c.execute("""
    delete from serialports where dev_id=?;
    """, [dev_id])
    _conn.commit()


def ip_version(addr):
    i = ipaddress.ip_address(addr)
    if type(i) is ipaddress.IPv4Address:
        return 4
    if type(i) is ipaddress.IPv6Address:
        return 6
    return None


if not is_schema_installed():
    raise Exception("server.db does not have schema configured")

