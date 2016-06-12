#! /usr/bin/env python3
import setuptools
import os

from  setuputils import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setuptools.setup(
    name = "PiCon Registration Agent",
    version = "0.0.1",
    author = "Team Kickass",
    author_email = "ryan@u13.net",
    description = ("PiCon registration agent for the PiCon console registry"),
    license = "BSD",
    keywords = "RaspberryPi Terminal Server Console",
    url = "http://nanog.org",
    packages=pkgs
    install_requires = ['daemonize','pyroute2','ipaddress','netifaces']
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
    ],
)
