# -*- coding: utf-8 -*-

from f5_agent_auditor import utils


class Tracer(object):

    def __init__(self, lbaas_manager, device_manager):
        self.lbaas_manager = lbaas_manager
        self.device_manager = device_manager

        self.db = self.lbaas_manager.db
        self.device_group = self.device_manager.device_group
        self.device = self.device_manager.device

    def set_agent_config(self):
        self.agent = self.device_manager.agent
        self.env_prefix = self.device_manager.partition_prefix + "_"

    @property
    def binding_info(self):
        return {
            "inventory": self.device_group["id"],
            "device": self.device["id"],
            "agent": self.agent["id"]
        }

    def get_uuid(self, name):
        return name.split("_")[1]

    def get_lbs_by_ids(self, ids):
        ret = []
        for lb_id in ids:
            lb = self.db.get_loadbalancer_by_id(lb_id)
            ret.append(lb)
        return ret

    def subnet_lbs(self, lb_dicts):
        ret = {}
        for lb in lb_dicts:
            subnet_id = lb["vip_subnet_id"]
            if subnet_id not in ret:
                ret[subnet_id] = [lb]
            else:
                ret[subnet_id].append(lb)
        return ret

    def net_lbs(self, lb_dicts):
        ret = {}
        for lb in lb_dicts:
            net_id = lb["network_id"]
            if net_id not in ret:
                ret[net_id] = [lb]
            else:
                ret[net_id].append(lb)
        return ret

    def id_res(self, res_dicts):
        return {res["id"]: res for res in res_dicts}

    def get_lbs_by_vlans(self, missing_vlans, vlans, lb_dicts):
        # vlan is unqiue for each project/partition
        ret = {}
        subnet_lbs = self.subnet_lbs(lb_dicts)

        for vlan_name in missing_vlans:
            vlan_subnets = vlans[vlan_name]
            loadbalancers = []
            ret[vlan_name] = loadbalancers
            for subnet_id in vlan_subnets:
                for lb in subnet_lbs.get(subnet_id, []):
                    lb.update(self.binding_info)
                    loadbalancers.append(lb)
        return ret

    def get_lbs_by_rds(self, missing_rds, rds, lb_dicts):
        # rds is unqiue for each project/partition
        ret = {}
        subnet_lbs = self.subnet_lbs(lb_dicts)

        for rds_name in missing_rds:
            rds_subnets = rds[rds_name]
            loadbalancers = []
            ret[rds_name] = loadbalancers
            for subnet_id in rds_subnets:
                for lb in subnet_lbs.get(subnet_id, []):
                    lb.update(self.binding_info)
                    loadbalancers.append(lb)
        return ret

    def get_lbs_by_gws(self, missing_gws, gws, lb_dicts):
        ret = {}
        # subnet_lbs = self.subnet_lbs(lb_dicts)
        net_lbs = self.net_lbs(lb_dicts)

        for gw_name in missing_gws:
            loadbalancers = []
            ret[gw_name] = loadbalancers

            gw_subnet = gws[gw_name]
            net_id = gw_subnet["network_id"]

            for lb in net_lbs.get(net_id, []):
                lb.update(self.binding_info)
                loadbalancers.append(lb)

        return ret

    def get_lbs_by_selfips(self, missing_selfips, selfips, lb_dicts):
        ret = {}
        net_lbs = self.net_lbs(lb_dicts)

        for selfip_name in missing_selfips:
            loadbalancers = []
            ret[selfip_name] = loadbalancers

            selfip_subnet = selfips[selfip_name]
            net_id = selfip_subnet["network_id"]

            # import pdb; pdb.set_trace()
            for lb in net_lbs.get(net_id, []):
                lb.update(self.binding_info)
                loadbalancers.append(lb)

        return ret

    def get_lbs_by_snatpools(self, missing_snatpools, lbs_dicts):
        ret = {}
        lbs = self.id_res(lbs_dicts)

        for snatpool_name in missing_snatpools:
            lb_id = utils.remove_prefix(snatpool_name)
            lb = lbs[lb_id]
            lb.update(self.binding_info)
            ret[snatpool_name] = lb

        return ret

    def get_lbs(self, missing_lbs, lbs_dicts):
        ret = {}
        lbs = self.id_res(lbs_dicts)

        for lb_name in missing_lbs:
            lb_id = utils.remove_prefix(lb_name)
            lb = lbs[lb_id]
            lb.update(self.binding_info)
            ret[lb_name] = lb

        return ret

    def get_lbs_by_listeners(self, missing_lss, id_lss, lbs):
        ret = {}
        lbs = self.id_res(lbs)
        for ls_name in missing_lss:
            ls = id_lss[ls_name]
            lb_id = ls["loadbalancer_id"]
            lb = lbs[lb_id]

            lb.update(self.binding_info)
            ret[ls_name] = lb

        return ret

    def get_lbs_by_pools(self, missing_pools, id_pools, lbs):
        ret = {}
        lbs = self.id_res(lbs)

        for pool_name in missing_pools:
            pool = id_pools[pool_name]
            lb_id = pool["loadbalancer_id"]
            lb = lbs[lb_id]

            lb.update(self.binding_info)
            ret[pool_name] = lb

        return ret

    def get_lbs_by_members(self, missing_members, id_members, pools, lbs):
        ret = {}
        lbs = self.id_res(lbs)
        pools = self.id_res(pools)

        for member_name in missing_members:
            member = id_members[member_name]

            pool_id = member["pool_id"]
            pool = pools[pool_id]

            lb_id = pool["loadbalancer_id"]
            lb = lbs[lb_id]

            lb.update(self.binding_info)
            ret[member_name] = lb

        return ret

    def get_lbs_by_monitors(self, missing_monitors, pools, lbs):
        ret = {}
        lbs = self.id_res(lbs)
        pools = {pool["healthmonitor_id"]: pool for pool in pools}

        for monitor_name in missing_monitors:
            monitor_id = utils.remove_prefix(monitor_name)
            # import pdb; pdb.set_trace()
            pool = pools[monitor_id]

            lb_id = pool["loadbalancer_id"]
            lb = lbs[lb_id]

            lb.update(self.binding_info)
            ret[monitor_name] = lb

        return ret

    def get_lbs_by_l7rules(self, missing_l7rules, id_l7rules,
                           l7policies, lss, lbs):
        ret = {}
        lbs = self.id_res(lbs)
        l7policies = {policy["id"]: policy for policy in l7policies}
        lss = {ls["id"]: ls for ls in lss}

        for l7rule_name in missing_l7rules:
            l7rule = id_l7rules[l7rule_name]
            l7policy_id = l7rule["l7policy_id"]

            l7policy = l7policies[l7policy_id]
            listener_id = l7policy["listener_id"]

            ls = lss[listener_id]
            lb_id = ls["loadbalancer_id"]

            lb = lbs[lb_id]
            lb.update(self.binding_info)
            ret[l7rule_name] = lb

        return ret
