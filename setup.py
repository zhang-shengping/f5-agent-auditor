# -*- coding: utf-8 -*-

import setuptools

setuptools.setup(
    install_requires=['f5-openstack-agent>=9.6.0'],
    # this works, but packages in setup.cfg not work
    packages=setuptools.find_packages()
)
