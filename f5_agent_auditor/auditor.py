# -*- coding: utf-8 -*-
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from f5_agent_auditor.db import LbaasDBResource
from f5_agent_auditor.manager.lbaas import Lbaas
from f5_agent_auditor.manager.device import Device
from f5_agent_auditor.tracer import Tracer
from f5_agent_auditor.rebuilder import Rebuilder
from f5_agent_auditor import utils

from f5_agent_auditor import options
from oslo_log import log as logging

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

from pprint import pformat

import time
import json
import psutil
import os

pid = os.getpid()

conf = options.cfg.CONF
logging.setup(conf, __name__)
LOG = logging.getLogger(__name__)


def expect(lbaas_names, bigip_names):
    notfound = set(lbaas_names) - set(bigip_names)
    return notfound


def unexpect(lbaas_names, bigip_names):
    notfound = set(bigip_names) - set(lbaas_names)
    return notfound


def log_missings(cache, res_type, res):
    cache[res_type] = res


BOLD = '\033[1m'
END = '\033[0m'


@utils.time_logger(LOG)
def main():

    LOG.info("Start auditing")

    LOG.info("Initate Comparator ...")

    LOG.info("Building Database connection for LBaaS Manager ...")
    lbaasDB = LbaasDBResource()

    LOG.info(
        "Initiate LBaaS Manager "
        "to build global bindings and projects resources index ..."
    )
    lbaas_manager = Lbaas(lbaasDB)

    # NOTE(pzhang): replace this binding_idx as a cache object
    # the cache object can be shared by other object service.
    # all binding {'device_group': {'device':{'agent'{'project':['lb_id']}}}}
    binding_idx = lbaas_manager.binding_idx

    # device id is not shared by device_group
    global_missing_info = {}

    for group_id in binding_idx:
        device_group = lbaas_manager.device_groups[group_id]

        # global_missing_info = {}

        for device_id in binding_idx[group_id]:

            LOG.info(
                "Initiate Device Manager "
                "for device %s" % device_id
            )
            device = lbaas_manager.devices[device_id]
            device_manager = Device(device_group, device)
            tracer = Tracer(lbaas_manager, device_manager)

            LOG.info(
                "{}Start auditing for bigip: {} hostname {}{}".format(
                    BOLD,
                    device_manager.device["mgmt_ipv4"],
                    device_manager.device_name,
                    END
                )
            )

            LOG.info("Start to auditing partitions for device: %s" % device_id)
            agent_projects = lbaas_manager.agents_projects(
                group_id, device_id)
            device_partitions = device_manager.dev_partitions()

            LOG.debug("Found partition in DB: %s" % pformat(agent_projects))
            LOG.debug("Found partition in Bigip: %s" % pformat(agent_projects))

            missing_partition = expect(
                agent_projects, device_partitions)
            unknown_partition = unexpect(
                agent_projects, device_partitions)

            # generate and download scf file
            # scf = device_manager.save_scf(directory="/var/local/scf/")
            # device_manager.mvto_bulk(scf)
            # device_manager.download_scf("default_auditor.scf")

            device_agents_projects = lbaas_manager.binding_idx[
                group_id][device_id]

            all_missing = {}
            for agent_id, projects_lbs in device_agents_projects.items():

                agent_missing = {}
                all_missing[agent_id] = agent_missing

                agent = lbaas_manager.agents[agent_id]
                LOG.info(
                    "Set Device Group and Agent config for Device Manager.\n"
                    "Device Group: %s\nAgent: %s\n" % (device_group, agent)
                )
                device_manager.set_device_config(agent)
                tracer.set_agent_config()

                for project_id, lbs in projects_lbs.items():
                    project_missing = {}
                    agent_missing[project_id] = project_missing

                    devhost = device_manager.device["mgmt_ipv4"]
                    # NOTE(pzhang) move attribute to device_manager
                    # at agent and device_group level
                    agent_env = device_manager.partition_prefix

                    current_partition = utils.partition_name(
                        agent_env, project_id)

                    if current_partition in missing_partition:
                        missing_partition_lbs = tracer.get_lbs_by_ids(lbs)

                        log_missings(
                            project_missing, "tenants",
                            missing_partition_lbs
                        )
                        continue

                    LOG.info(
                        "{}Start to auditing the details for DEVICE: {}, "
                        "Partition: {}_{}, LOADBALANCERS: {}{}".format(
                            BOLD,
                            devhost, agent_env, project_id, lbs,
                            END
                        )
                    )
                    # chek network reosurces

                    # subnet cache
                    project_nets = lbaas_manager.dev_agent_project_nets(
                        lbs)

                    LOG.info(
                        "Start to gather netconf: Vlans, Routedomains, "
                        "Selfips, Gateways."
                    )
                    device_name = device_manager.device_name
                    vtep_ip = device_manager.node_vtep_ip
                    vlans, rds, selfips, gateways = \
                        lbaas_manager.dev_agent_project_netconf(
                            device_name, agent_env, vtep_ip, project_nets)

                    LOG.info("Start to auditing vlan")
                    partition_vlans = device_manager.dev_partition_vlans(
                        project_id)
                    LOG.debug("Found vlan in DB: %s" % pformat(vlans))
                    LOG.debug("Found vlan in Bigip: %s" % pformat(partition_vlans))

                    lb_dicts = lbaas_manager.get_lbs_dicts(lbs)

                    missing_vlans = expect(vlans.keys(), partition_vlans)
                    missing_vlan_lbs = tracer.get_lbs_by_vlans(
                        missing_vlans, vlans, lb_dicts)

                    if missing_vlan_lbs:
                        log_missings(
                            project_missing, "vlans",
                            missing_vlan_lbs
                        )

                    LOG.info("Start to auditing route domain")
                    partition_rds = device_manager.dev_partition_rds(
                        project_id)
                    LOG.debug("Found route domain in DB: %s" % pformat(rds))
                    LOG.debug("Found route domain in Bigip: %s" % pformat(partition_rds))

                    missing_rds = expect(rds.keys(), partition_rds)
                    missing_rd_lbs = tracer.get_lbs_by_rds(
                        missing_rds, rds, lb_dicts)

                    if missing_rd_lbs:
                        log_missings(
                            project_missing, "routedomains",
                            missing_rd_lbs
                        )

                    LOG.info("Start to auditing gateways")
                    partition_gws = device_manager.dev_partition_gateways(
                        project_id)
                    LOG.debug("Found gateway in DB: %s" % pformat(gateways))
                    LOG.debug("Found gateway in Bigip: %s" % pformat(partition_gws))

                    missing_gateways = expect(gateways.keys(), partition_gws)
                    missing_gateway_lbs = tracer.get_lbs_by_gws(
                        missing_gateways, gateways, lb_dicts)

                    if missing_gateway_lbs:
                        log_missings(
                            project_missing, "gateways",
                            missing_gateway_lbs
                        )

                    LOG.info("Start to auditing selfip")
                    partition_selfips = device_manager.dev_partition_selfips(
                        project_id)
                    LOG.debug("Found selfip in DB: %s" % pformat(selfips))
                    LOG.debug("Found selfip in Bigip: %s" % pformat(partition_selfips))

                    missing_selfips = expect(
                        selfips.keys(), partition_selfips)
                    missing_selfip_lbs = tracer.get_lbs_by_selfips(
                        missing_selfips, selfips, lb_dicts)

                    if missing_selfip_lbs:
                        log_missings(
                            project_missing, "selfips",
                            missing_selfip_lbs
                        )

                    LOG.info("Start to auditing snatpool")
                    project_snatpools = lbaas_manager.agent_project_snatpools(
                        agent_env, lbs
                    )
                    partition_snatpools = \
                        device_manager.dev_partition_snatpools(
                            project_id
                        )
                    LOG.debug("Found snatpool in DB: %s" % pformat(project_snatpools))
                    LOG.debug("Found snatpool in Bigip: %s" % pformat(partition_snatpools))

                    missing_snatpools = expect(
                        project_snatpools, partition_snatpools)
                    missing_snatpool_lbs = tracer.get_lbs_by_snatpools(
                        missing_snatpools, lb_dicts)

                    if missing_snatpool_lbs:
                        log_missings(
                            project_missing, "snatpools",
                            missing_snatpool_lbs
                        )

                    # check loadbalancers
                    # we do not have to find loadbalancers, so do not cache
                    # loadbalancer object.
                    # when it is absent, we find the absent in DB
                    LOG.info("Start to auditing loadbalancer")
                    project_loadbalancers = \
                        lbaas_manager.agent_project_loadbalancers(
                            agent_env, lbs)
                    partition_vips = device_manager.dev_partition_vips(
                        project_id)

                    LOG.debug("Found loadbalancer in DB: %s" % pformat(project_loadbalancers))
                    LOG.debug("Found loadbalancer in Bigip: %s" % pformat(partition_vips))

                    missing_loadbalancers = expect(
                        project_loadbalancers, partition_vips)
                    missing_lbs = tracer.get_lbs(
                        missing_loadbalancers, lb_dicts)

                    if missing_lbs:
                        log_missings(
                            project_missing, "loadbalancers",
                            missing_lbs
                        )

                    # chek listeners

                    # we have to find listeners, so cache listeners dict.
                    # when a listener is absent, we trace it in cache.
                    LOG.info("Start to auditing listener")
                    lbaas_listeners = lbaas_manager.get_listeners(lbs)

                    project_listeners = lbaas_manager.agent_project_listeners(
                        agent_env, lbaas_listeners)
                    partition_vss = device_manager.dev_partition_vss(
                        project_id)

                    LOG.debug("Found listener in DB: %s" % pformat(project_listeners))
                    LOG.debug("Found listener in Bigip: %s" % pformat(partition_vss))

                    missing_listeners = expect(
                        project_listeners.keys(), partition_vss)
                    missing_listener_lbs = tracer.get_lbs_by_listeners(
                        missing_listeners, project_listeners, lb_dicts)

                    if missing_listener_lbs:
                        log_missings(
                            project_missing, "listeners",
                            missing_listener_lbs
                        )

                    # chek pools, member, monitors

                    LOG.info("Start to auditing pool")
                    lbaas_pools = lbaas_manager.get_pools(lbs)
                    dev_pools = device_manager.get_pools(project_id)

                    # pool cache
                    project_pools = lbaas_manager.agent_project_pools(
                        agent_env, lbaas_pools
                    )
                    partition_pools = device_manager.dev_partition_pools(
                        dev_pools
                    )
                    LOG.debug("Found pool in DB: %s" % pformat(project_pools))
                    LOG.debug("Found pool in Bigip: %s" % pformat(partition_pools))

                    missing_pools = expect(
                        project_pools.keys(), partition_pools)
                    missing_pool_lbs = tracer.get_lbs_by_pools(
                        missing_pools, project_pools, lb_dicts)

                    if missing_pool_lbs:
                        log_missings(
                            project_missing, "pool",
                            missing_pool_lbs
                        )

                    LOG.info("Start to auditing pool memeber")
                    # member cache
                    project_members = lbaas_manager.agent_project_members(
                        agent_env, project_pools
                    )
                    partition_members = device_manager.dev_partition_members(
                        dev_pools
                    )

                    LOG.debug("Found member in DB: %s" % pformat(project_members))
                    LOG.debug("Found member in Bigip: %s" % pformat(partition_members))

                    missing_members = expect(
                        project_members.keys(), partition_members)
                    missing_member_lbs = tracer.get_lbs_by_members(
                        missing_members, project_members,
                        lbaas_pools, lb_dicts)

                    if missing_member_lbs:
                        log_missings(
                            project_missing, "member",
                            missing_member_lbs
                        )

                    LOG.info("Start to auditing pool monitor")
                    project_monitors = lbaas_manager.agent_project_monitors(
                        agent_env, project_pools
                    )
                    partition_monitors = device_manager.dev_partition_monitors(
                        project_id)

                    LOG.debug("Found monitor in DB: %s" % pformat(project_monitors))
                    LOG.debug("Found monitor in Bigip: %s" % pformat(partition_monitors))

                    missing_monitors = expect(
                        project_monitors, partition_monitors)
                    missing_monitor_lbs = tracer.get_lbs_by_monitors(
                        missing_monitors, lbaas_pools, lb_dicts)

                    if missing_monitor_lbs:
                        log_missings(
                            project_missing, "healthmonitor",
                            missing_monitor_lbs
                        )

                    LOG.info("Start to auditing l7rules")
                    lbaas_l7policies = lbaas_manager.get_l7policies(
                        lbaas_listeners)
                    project_l7rules = lbaas_manager.agent_project_l7rules(
                        lbaas_l7policies
                    )
                    partition_irules = device_manager.dev_partition_irules(
                        project_id)

                    LOG.debug("Found l7rule in DB: %s" % pformat(project_l7rules))
                    LOG.debug("Found irule in Bigip: %s" % pformat(partition_irules))

                    missing_l7rules = expect(
                        project_l7rules, partition_irules)
                    missing_l7rule_lbs = tracer.get_lbs_by_l7rules(
                        missing_l7rules, project_l7rules,
                        lbaas_l7policies, lbaas_listeners, lb_dicts)

                    if missing_l7rule_lbs:
                        log_missings(
                            project_missing, "l7rule",
                            missing_l7rule_lbs
                        )

            device_host = device_manager.device["mgmt_ipv4"]
            filepath = "/tmp/" + utils.timestamp_filename(device_host)
            with open(filepath, "w") as log_file:
                json.dump(all_missing, log_file, ensure_ascii=False, indent=4)

            LOG.info("Auditor file %s has been created" % filepath)

            global_missing_info[device_id] = all_missing

    LOG.info("Initiate Rebuilder with keystone admin file %s" %
             conf.rcfile_path)
    rebuilder = Rebuilder(global_missing_info, conf.rcfile_path)

    bash_script = rebuilder.generate_bash()
    if bash_script:
        LOG.info("Create rebuild bash script %s" % bash_script)

    if bash_script and conf.rebuild:
        LOG.info("Run rebuild bash script %s" % bash_script)
        rebuilder.run_bash(bash_script)


if __name__ == "__main__":
    main()
