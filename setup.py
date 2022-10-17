# -*- coding: utf-8 -*-

import setuptools

import codecs
import os.path

def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), 'r') as fp:
        return fp.read()

def get_version(rel_path):
    for line in read(rel_path).splitlines():
        if line.startswith('__version__'):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError("Unable to find version string.")

setuptools.setup(
    install_requires=['f5-openstack-agent>=9.6.0'],

    # if setuptools (easy_install) version is less than
    # setuptools 30.3.0, the setup.cfg file would work.
    # define minimal configuration here.
    name = "f5-agent-auditor",
    version=get_version("f5_agent_auditor/__init__.py"),
    entry_points = {
        'console_scripts': [
            'f5-agent-auditor = f5_agent_auditor.auditor:main'
        ]
    },
    # set to not install as a egg
    zip_safe=False,
    # this works, but packages in setup.cfg not work
    packages=setuptools.find_packages()
)
