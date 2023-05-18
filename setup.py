# -*- coding: utf-8 -*-

import setuptools

setuptools.setup(

    # if setuptools (easy_install) version is less than
    # setuptools 30.3.0, the setup.cfg file would work.
    # define minimal configuration here.
    name = "f5-agent-auditor",
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
