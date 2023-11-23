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

from f5_agent_auditor import utils
from oslo_log import log as logging

LOG = logging.getLogger(__name__)


# TODO(pzhang): the cache may be a individal service object
def add_cache(ca, identity, obj):
    if identity not in ca:
        ca[identity] = obj


def get_vtep_vlan(network, vtep_node_ip):
    vlanid = None
    default_vlanid = None
    segments = network.get('segments', [])

    for seg in segments:
        phy_net = seg["provider:physical_network"]
        vlanid = seg["provider:segmentation_id"]

        if phy_net == "default":
            default_vlanid = vlanid
        if phy_net is not None and phy_net == vtep_node_ip:
            return vlanid

    if default_vlanid is not None:
        return default_vlanid

    return network['provider:segmentation_id']


class Lbaas(object):
    """ Cache everything when it is found"""

    def __init__(self, source):
        self.db = source

        self.bindings = []
        self.device_groups = {}
        self.devices = {}
        self.agents = {}
        # self.loadbalancers = {}

        self.binding_idx = self.build_binding_index()

    @utils.time_logger(LOG)
    def build_binding_index(self):
        """return {'device_group': {'device':{'agent'{'project':['lb_id']}}}}
        """

        tree = {}

        self.bindings = self.db.get_bindings()

        for bind in self.bindings:

            device_group_id = bind["device_id"]
            agent_id = bind["agent_id"]
            lb_id = bind["loadbalancer_id"]

            loadbalancer = self.db.get_loadbalancer_by_id(lb_id)
            project_id = loadbalancer['project_id']
            # add_cache(self.loadbalancers,
                      # loadbalancer["id"], loadbalancer)

            if not (device_group_id and agent_id and lb_id):
                LOG.ERROR("bind %s is misdata for binding tree.")

            devices = []
            if device_group_id not in tree:
                tree[device_group_id] = {}

                device_group = self.db.get_device_group_by_id(device_group_id)
                add_cache(self.device_groups, device_group_id, device_group)

                devices = self.db.get_devices_by_group_id(device_group_id)
            else:
                devices = self.db.get_devices_by_group_id(device_group_id)

            # bigip device
            for dev in devices:
                dev_id = dev["id"]

                if dev_id not in tree[device_group_id]:
                    tree[device_group_id][dev_id] = {}

                    add_cache(self.devices, dev_id, dev)

                if agent_id not in tree[device_group_id][dev_id]:
                    tree[device_group_id][dev_id][agent_id] = {}

                    agent = self.db.get_agent_by_id(agent_id)
                    add_cache(self.agents, agent["id"], agent)

                if project_id not in tree[device_group_id][dev_id][
                        agent_id]:
                    tree[device_group_id][dev_id][agent_id][project_id] = []

                tree[device_group_id][dev_id][agent_id][project_id].append(
                    lb_id)

        return tree

    # TODO(pzhang): add cache for db
    def _get_subnet_by_lbid(self, lb_id):
        ret = {}

        lb = self.db.get_loadbalancer_by_id(lb_id)
        subnet_id = lb["vip_subnet_id"]
        ret = self.db.get_subnet_by_id(subnet_id)

        return ret

    def _get_segnet_by_subnet(self, subnet):
        ret = {}

        net_id = subnet["network_id"]
        net = self.db.get_net_by_id(net_id)
        segments = self.db.get_segments_by_net_id(net_id)
        net['segments'] = {seg['physical_network']: seg for seg in segments}
        ret = net

        return ret

    def agents_projects(self, dev_group, dev_id):
        """Get all projects of all agents in one bigip device.
        """
        ret = []

        devices = self.binding_idx[dev_group]
        agents_projects_lbs = devices[dev_id]

        for agent_id, projects_lbs in agents_projects_lbs.items():
            agent = self.agents[agent_id]
            if not agent:
                LOG.debug(
                    "Cannot find agent_id %s in agents cache, "
                    "now get it from DB." % agent_id
                )
                agent = self.db.get_agent_by_id(agent_id)
            env_prefix = agent["configurations"]["environment_prefix"]

            for project_id in projects_lbs.keys():
                partition = utils.partition_name(env_prefix, project_id)
                # NOTE duplicate value means some agents have the same prefix
                ret.append(partition)

        return ret

    def dev_agent_project_nets(self, project_lbs):

        ret = {}

        # TODO(pzhang): add cache for db
        for lb_id in project_lbs:
            subnet = self._get_subnet_by_lbid(lb_id)
            net = self._get_segnet_by_subnet(subnet)
            subnets = self.db.get_subnet_by_netid(net["id"])
            if len(subnets) > 2:
                raise Exception(
                    "The Netowrk %s has Subnets are more than 2.\n"
                    "Subnets: %s\n." % (net["id"], subnets)
                )
            net["subnets"] = {subnet["id"]: subnet for subnet in subnets}

            if net["id"] not in ret:
                ret[net["id"]] = net

        return ret

    def dev_agent_project_netconf(
            self, device_name, agent_env, vtep_ip, project_nets):
        """Return selfips, vlans, route domain, gateways of all
        networks.
        """
        vlans = {}
        rds = {}
        selfips = {}
        gateways = {}

        for net in project_nets.values():
            seg_id = utils.get_vlan_segid(vtep_ip, net)
            vlan = utils.vlan_name(seg_id)
            rd = utils.rd_name(agent_env, net["id"])
            subnets = net["subnets"]

            vlans[vlan] = subnets
            rds[rd] = subnets

            for subnet_id, subnet in subnets.items():
                selfip = utils.selfip_name(device_name, subnet_id)
                selfips[selfip] = subnet

                gateway_ip = subnet["gateway_ip"]
                gateway = utils.gatewy_name(gateway_ip, seg_id)
                gateways[gateway] = subnet

        return vlans, rds, selfips, gateways

    def agent_project_loadbalancers(self, agent_env, lbs):
        ret = []

        for lb_id in lbs:
            lb = utils.res_name(agent_env, lb_id)
            ret.append(lb)

        return ret

    def agent_project_snatpools(self, agent_env, lbs):
        ret = []

        for lb_id in lbs:
            lb = utils.res_name(agent_env, lb_id)
            ret.append(lb)

        return ret

    def get_listeners(self, lbs):
        ret = []
        for lb_id in lbs:
            ret += self.db.get_listeners_by_lbid(lb_id)
        return ret

    def agent_project_listeners(self, agent_env, listeners):
        ret = {utils.res_name(agent_env, ls["id"]): ls for ls in listeners}
        return ret

    def get_pools(self, lbs):
        ret = []

        for lb_id in lbs:
            ret += self.db.get_pools_by_lbid(lb_id)

        return ret

    def agent_project_pools(self, agent_env, pools):
        ret = {utils.res_name(agent_env, pl["id"]): pl for pl in pools}
        return ret

    def agent_project_members(self, agent_env, pools):
        ret = {}

        for pl in pools.values():
            members = self.db.get_members_by_plid(pl["id"])
            mbs_dict = {
                utils.res_name(agent_env, mb["id"]): mb for mb in members}
            ret.update(mbs_dict)
        return ret

    def agent_project_monitors(self, agent_env, pools):
        ret = []

        for pl in pools.values():
            ret.append(utils.res_name(agent_env, pl["healthmonitor_id"]))
            # monitor_id = pl["healthmonitor_id"]
            # ret[utils.res_name(agent_env, pl["healthmonitor_id"])] = \
                # self.db.get_monitors_by_id(monitor_id)
        return ret

    def get_l7policies(self, listeners):
        ret = []

        # TODO: we may can fetchall in IDs from DB
        for ls in listeners:
            ret += self.db.get_policies_by_lsid(ls["id"])

        return ret

    def agent_project_l7rules(self, policies):
        ret = {}
        prefix = "irule"

        for policy in policies:
            l7rules = []
            l7rules = self.db.get_l7rules_by_polid(
                policy["id"]
            )
            rules_dict = {utils.res_name(prefix, rule["id"]): rule
                          for rule in l7rules}
            ret.update(rules_dict)

        return ret

    def get_lbs_dicts(self, lb_ids):
        ret = []

        for lb_id in lb_ids:
            lb_dict = self.db.get_loadbalancer_by_id(lb_id)
            subnet_id = lb_dict["vip_subnet_id"]
            subnet = self.db.get_subnet_by_id(subnet_id)
            lb_dict["network_id"] = subnet["network_id"]
            ret.append(lb_dict)
        return ret
