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

import netaddr


class BigIPFilter(object):

    @staticmethod
    def format_selfips(sep, selfips):
        result = dict()

        for selfip in selfips:
            subnet_id = selfip.name.split(sep)[1]
            result[subnet_id] = selfip.address

        return result

    @staticmethod
    def format_vlans(vlans):
        result = list()

        for vlan in vlans:
            result.append(vlan.tag)

        return result

    @staticmethod
    def format_rds(rds):
        result = list()

        for rd in rds:
            result.append(rd.id)

        return result

    @staticmethod
    def format_routes(routes):
        result = dict()

        for route in routes:
            result[route.name] = route.gw

        return result

    def __init__(self, prefix):
        self.prefix = prefix + "_"

    def get_id(self, resource):
        uuid = resource.name.split(self.prefix)[-1]
        return uuid

    def get_ids(self, resources):
        ids = []
        for res in resources:
            if self.prefix in res.name:
                uuid = self.get_id(res)
                ids.append(uuid)
        return set(ids)

    def filter_loadbalancers(self, loadbalancers):
        balancers = {}
        for lb in loadbalancers:
            balancers[self.get_id(lb)] = lb.address
        return balancers

    @staticmethod
    def format_member(member):
        # address = None
        # port = None
        mb = member.get('name')

        if mb == []:
            return

        return mb

    def filter_pool_members(self, partition_pools):
        pools = {}
        for pl in partition_pools:
            members = []
            pl_id = None
            member_items = pl.membersReference.get('items')
            if member_items:
                for mb in member_items:
                    member = self.format_member(mb)
                    if member is not None:
                        members.append(member)
            pl_id = self.get_id(pl)
            pools[pl_id] = members
        return pools


class LbaasFilter(object):

    def get_resources(self, resources):
        result = {}
        for res in resources:
            result[res.id] = res
        return result

    @staticmethod
    def format_member(member):
        mb = {}

        addr = member.address.split("%")
        ip = netaddr.IPAddress(addr[0])
        if ip.version == 6:
            mb['address_port'] = member.address + "." + str(member.protocol_port)
        else:
            mb['address_port'] = member.address + ":" + str(member.protocol_port)

        mb['id'] = member.id
        mb['provisioning_status'] = member.provisioning_status
        mb['project_id'] = member.project_id
        mb['bigip_ips'] = []
        return mb

    @staticmethod
    def format_project_nets_subnets(project_nets):

        # this function use project_nets to resolve
        # net, subnet and route of each project

        if not project_nets:
            return dict(), dict(), dict()

        net_ret = dict()
        subnet_ret = dict()
        vlan_seg = ""
        route_ret = dict()

        for net in project_nets.values():
            if net.project_id not in net_ret:
                net_ret[net.project_id] = dict()

            net_segs = net_ret[net.project_id]
            segment_id = ""
            for seg in net.segments:
                if seg.network_type == "vlan":
                    segment_id = seg.segmentation_id
                    net_segs[segment_id] = {
                        "resource type": "vlan",
                        "uuid": net.id,
                        "project id": net.project_id,
                        "detail": {
                            "id": net.id,
                            "project_id": net.project_id,
                            "name": net.name,
                            "status": net.status,
                            "admin_state_up": net.admin_state_up,
                            "vlan_segment": seg.segmentation_id,
                            "mtu": net.mtu,
                            "vlan_transparent": net.vlan_transparent,
                            "availability_zone_hints": net.availability_zone_hints
                        }
                    }
                    vlan_seg = seg.segmentation_id

            if net.project_id not in subnet_ret:
                subnet_ret[net.project_id] = dict()
                route_ret[net.project_id] = dict()

            subnets = subnet_ret[net.project_id]
            routes = route_ret[net.project_id]
            gateway_suffix = "_default_route_" + str(vlan_seg)

            for subnet in net.subnet_infos:
                subnet_detail = {
                    "id": subnet.id,
                    "project_id": subnet.project_id,
                    "name": subnet.name,
                    "cidr": subnet.cidr,
                    "gateway_ip": subnet.gateway_ip,
                    "ip_version": subnet.ip_version,
                    "network_id": subnet.network_id,
                    "segment_id": segment_id
                }

                subnet_info = {
                    "resource type": "selfip",
                    "uuid": subnet.id,
                    "project id": subnet.project_id,
                    "detail": subnet_detail}
                subnets[subnet.id] = subnet_info

                # ip_version = netaddr.IPAddress(
                    # subnet.gateway_ip).version
                gateway_name = "IPv" + str(
                    subnet.ip_version) + gateway_suffix
                routes.update(
                    {
                        gateway_name:{
                            "resource type": "gateway",
                            "uuid": gateway_name,
                            "detail": subnet_detail
                        }
                    }
                )

        return net_ret, subnet_ret, route_ret

    @staticmethod
    def format_routes(routes):
        if not routes:
            return list()

    @staticmethod
    def format_vlans(vlans):
        if not vlans:
            return list()

    @staticmethod
    def format_rds(rds):
        if not rds:
            return list()

    def filter_pool_members(self, project_pools):
        pools = {}
        for pl in project_pools:
            members = []
            for mb in pl.members:
                member = self.format_member(mb)
                members.append(member)
            pools[pl.id] = members
        return pools

    def convert_projects(self, diff_ids):
        res = [
            {
                "resource type": "project",
                "uuid": uuid,
            }
            for uuid in diff_ids
        ]
        return res

    # pzhang convert format
    def convert_common_resources(self,
                                 diff_ids,
                                 resources,
                                 resource_type=None):
        res = [
            {
                "resource type": resource_type,
                "uuid": uuid,
                "provisioning status": resources[
                    uuid].provisioning_status,
                "project id": resources[
                    uuid].project_id
            }
            for uuid in diff_ids
        ]
        return res

    def convert_loadbalancers(self, balancer, bigip_ip):
        lb = {
            "resource type": "loadbalancer",
            "uuid": balancer.id,
            "provisioning status": balancer.provisioning_status,
            "project id": balancer.project_id,
            "detail": {
                "address": balancer.vip_address,
            },
        }

        return lb

    # pzhang convert format
    def convert_members(self, pool_id, members):
        mbs = [{
            "resource type": "member",
            "uuid": m['id'],
            "provisioning status": m['provisioning_status'],
            "project id": m["project_id"],
            "pool id": pool_id,
            "detail": m['address_port'],
        } for m in members]

        return mbs
