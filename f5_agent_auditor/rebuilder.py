# -*- coding: utf-8 -*-

from f5_agent_auditor import utils
from jinja2 import Environment, FileSystemLoader

import os
import subprocess


class Rebuilder(object):

    def __init__(self, missing_info, rcfile):
        """{
            "device_id":{
                "agent_id":{
                    "project_id":{
                        "resource_name":{} or []
                    }
                }
            }
        }
        """
        self.missing_info = missing_info
        if not rcfile:
            raise Exception(
                "Please provider keystone admin rcfile")
        self.rcfile = rcfile

        self.loadbalancers = self.filter_loadbalancers()

    def filter_loadbalancers(self):
        rebuild_lbs = {}

        for agent in self.missing_info.values():
            for project in agent.values():
                for resource in project.values():
                    for lbs in resource.values():
                        # for tenants
                        if isinstance(lbs, list):
                            rebuild_lbs.update(
                                {lb["id"]: lb for lb in lbs}
                            )
                        if isinstance(lbs, dict):
                            for key, value in lbs.items():
                                if value:
                                    # for selfips, gateway, route
                                    if isinstance(value, list):
                                        rebuild_lbs.update(
                                            # {v["id"]: v for v in value}
                                            # only take one sample lb
                                            # to rebuild.
                                            {value[0]["id"]: value[0]}
                                        )
                                    # for lb, member, listener ...
                                    if isinstance(value, dict):
                                        rebuild_lbs.update(
                                            {value["id"]: value})

        # for key for set
        return rebuild_lbs.values()

    def generate_bash(self):
        if self.loadbalancers:
            tmpl_path = os.path.join(os.path.dirname(__file__), "templates/")
            environment = Environment(loader=FileSystemLoader(tmpl_path))
            template = environment.get_template("rebuild_all.tmpl")
            context = {
                "loadbalancers": self.loadbalancers,
                "rcfile": self.rcfile
            }
            content = template.render(context)
            filepath = "/tmp/" + utils.timestamp_bash("rebuild_all")

            with open(filepath, "w") as bashfile:
                bashfile.write(content)
            os.chmod(filepath, 0o755)

            return filepath

    def run_bash(self, script):
        rc = subprocess.call(script)
        if rc == 0:
            pass
        else:
            pass
