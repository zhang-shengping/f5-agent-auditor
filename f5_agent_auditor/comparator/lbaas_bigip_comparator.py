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

from icontrol.exceptions import iControlUnexpectedHTTPError
import copy

class LbaasToBigIP(object):

    def __init__(self, benchmark, benchmark_filter):

        self.benchmark_name = None
        self.benchmark = None
        self.benchmark_filter = None
        self.benchmark_projects = None

        self.subject_name = None
        self.subject = None
        self.subject_filter = None
        self.subject_projects = None

        self.validate_subject(benchmark)
        self.init_benchmark(benchmark, benchmark_filter)

    def compare_to(self, subject, subject_filter):
        self.validate_subject(subject)
        self.init_subject(subject, subject_filter)

    def validate_subject(self, subject):
        if not isinstance(subject, dict):
            raise Exception("Comparator must be a dcit type")
        if len(subject) != 1:
            raise Exception("Only one Comparator should be "
                            "provided at a time")

    def init_subject(self, subject, subject_filter):
        self.subject_name = subject.keys()[0]
        self.subject = subject.values()[0]

        self.subject_filter = subject_filter
        projects = self.subject.get_projects_on_device()
        self.subject_projects = self.subject_filter.get_ids(
            projects
        )

    def init_benchmark(self, benchmark, benchmark_filter):
        self.benchmark_name = benchmark.keys()[0]
        self.benchmark = benchmark.values()[0]
        self.benchmark_filter = benchmark_filter

        projects = \
            self.benchmark.get_projects_on_device()
        self.benchmark_projects = set(projects)

    def get_common_resources_diff(self, bm_resources,
                                  sub_method,
                                  resource_type=None):
        sub_resources = []

        bm_res = self.benchmark_filter.get_resources(
            bm_resources)
        bm_ids = set(bm_res.keys())

        for project in self.subject_projects:
            sub_resources += sub_method(
                project
            )

        sub_ids = self.subject_filter.get_ids(
            sub_resources)

        diff = bm_ids - sub_ids

        result = self.benchmark_filter.convert_common_resources(
            diff, bm_res, resource_type=resource_type
        )

        return result

    def get_missing_projects(self):
        res = self.benchmark_projects - self.subject_projects
        diff = self.benchmark_filter.convert_projects(
            res
        )
        return diff

    def get_missing_loadbalancers(self):
        lb_resources = []
        sub_resources = []
        missing = []
        converted_lb = {}

        for project in self.benchmark_projects:
            lb_resources += self.benchmark.get_agent_project_loadbalancers(
                project
            )

        for project in self.subject_projects:
            sub_resources += self.subject.get_project_loadbalancers(
                project
            )

        bigip_lbs = self.subject_filter.filter_loadbalancers(sub_resources)

        for lb in lb_resources:
            if lb.id not in bigip_lbs:
                converted_lb = self.benchmark_filter.convert_loadbalancers(
                    lb, ""
                )
                missing.append(converted_lb)
            else:
                bigip_ip = bigip_lbs[lb.id]
                if lb.vip_address != bigip_ip:
                    converted_lb = self.benchmark_filter.convert_loadbalancers(
                        lb, bigip_ip
                    )
                    missing.append(converted_lb)

        return missing

    def get_missing_listeners(self):
        lb_resources = []
        for project in self.benchmark_projects:
            lb_resources += self.benchmark.get_agent_project_loadbalancers(
                project
            )

        ls_resources = []
        lb_ids = [lb.id for lb in lb_resources]
        ls_resources += self.benchmark.get_listeners_by_lb_ids(lb_ids)

        sub_method = self.subject.get_project_listeners
        diff = self.get_common_resources_diff(
            ls_resources, sub_method, "listener"
        )
        return diff

    def get_missing_pools(self):
        lb_resources = []
        for project in self.benchmark_projects:
            lb_resources += self.benchmark.get_agent_project_loadbalancers(
                project
            )

        pl_resources = []
        lb_ids = [lb.id for lb in lb_resources]
        pl_resources += self.benchmark.get_pools_by_lb_ids(lb_ids)

        sub_method = self.subject.get_project_pools
        diff = self.get_common_resources_diff(
            pl_resources, sub_method, "pool"
        )
        return diff

    def get_missing_members(self):
        bm_lbs = []
        bm_pools = []
        sub_pools = []
        missing_mb = []

        for project in self.benchmark_projects:
            bm_lbs += self.benchmark.get_agent_project_loadbalancers(
                project
            )

        lb_ids = [lb.id for lb in bm_lbs]
        bm_pools += self.benchmark.get_pools_by_lb_ids(lb_ids)
        bm_mbs = self.benchmark_filter.filter_pool_members(bm_pools)

        for project in self.subject_projects:
            sub_pools += self.subject.get_project_pools(
                project
            )

        sub_mbs = self.subject_filter.filter_pool_members(sub_pools)

        for pool_id, members in bm_mbs.items():
            if pool_id not in sub_mbs:
                if members:
                    missing_mb += self.benchmark_filter.convert_members(
                        pool_id, members)
                continue

            for mb in members:
                if not mb["address_port"] in sub_mbs[pool_id]:
                    mb['bigip_ips'] = sub_mbs[pool_id]
                    missing_mb += self.benchmark_filter.convert_members(
                        pool_id, [mb])

        return missing_mb


class NetworkLbaasToBigIP(LbaasToBigIP):
    def __init__(self, benchmark, benchmark_filter):
        super(NetworkLbaasToBigIP, self).__init__(
            benchmark, benchmark_filter
        )

        self.benchmark_nets = self._get_benchmark_nets()
        self._format_project_net_info()

    def _get_benchmark_nets(self):
        bm_nets = dict()

        for project_id in self.benchmark_projects:
            if project_id not in bm_nets:
                nets = self.benchmark.get_project_net_info(
                    project_id
                )
                bm_nets.update(nets)
        return bm_nets

    def _format_project_net_info(self):
        self.project_nets, self.project_subnets, self.project_routes = \
            self.benchmark_filter.format_project_nets_subnets(
                self.benchmark_nets
            )

    def get_project_selfips(self):
        sub_selfips = dict()

        for project_id in self.benchmark_projects:
            if project_id not in sub_selfips:
                selfips = self.subject.get_project_selfips(
                    project_id
                )
                if self.subject.device_name is not "":
                    separator = self.subject.device_name + "-"
                # format selfips
                sub_selfips[
                    project_id
                ] = self.subject_filter.format_selfips(
                    separator, selfips)

        return sub_selfips

    def get_project_rds(self):
        sub_rds = dict()

        for project_id in self.benchmark_projects:
            if project_id not in sub_rds:
                rds = self.subject.get_project_rds(
                    project_id
                )
                # format rds
                sub_rds[
                    project_id
                ] = self.subject_filter.format_rds(rds)

        return sub_rds

    def get_project_vlans(self):
        sub_vlans = dict()

        for project_id in self.benchmark_projects:
            if project_id not in sub_vlans:
                vlans = self.subject.get_project_vlans(
                    project_id
                )
                # format vlans
                sub_vlans[
                    project_id
                ] = self.subject_filter.format_vlans(vlans)

        return sub_vlans

    def get_project_routes(self):
        sub_routes = dict()

        for project_id in self.benchmark_projects:
            if project_id not in sub_routes:
                routes = self.subject.get_project_routes(
                    project_id
                )
                # format routes
                sub_routes[
                    project_id
                ] = self.subject_filter.format_routes(routes)

        return sub_routes

    def _is_dict_res(self, *args):
        ret = list()
        for resources in args:
            ret += [isinstance(res, dict) for res in resources]
        return all(ret)

    def _find_missing_res(self, lbaas_project_res, bigip_project_res):
        missing = list()
        for project_id in lbaas_project_res:
            if project_id not in bigip_project_res:
                missing_res = lbaas_project_res[project_id]
                missing += missing_res.values()
            else:
                lbaas_res = lbaas_project_res[project_id]
                bigip_res = bigip_project_res[project_id]
                if self._is_dict_res(lbaas_res, bigip_res):
                    missing_ids = set(lbaas_res.keys()) - set(bigip_res.keys())
                else:
                    missing_ids = set(lbaas_res) - set(bigip_res)
                for indx in missing_ids:
                    missing.append(lbaas_res[indx])
        return missing

    # check bigp ip selfip
    def get_missing_selfip(self):
        missing = list()
        if self.project_subnets:
            # bigip partition's selfip
            subject_selfips = self.get_project_selfips()
            missing = self._find_missing_res(self.project_subnets,
                                             subject_selfips)
        return missing

    def get_missing_route(self):
        missing = list()
        if self.project_routes:
            subject_routes = self.get_project_routes()
            missing = self._find_missing_res(self.project_routes,
                                             subject_routes)
        return missing

    def get_missing_route_domain(self):
        missing = list()
        if self.project_nets:
            subject_rds = self.get_project_rds()

            for project_id in self.project_nets:
                if project_id not in subject_rds:
                    for rd in self.project_nets[project_id].values():
                        tmp = copy.deepcopy(rd)
                        tmp["resource type"] = "route domain"
                        missing.append(tmp)
                else:
                    lbaas_rds = self.project_nets[project_id]
                    bigip_rds = subject_rds[project_id]
                    missing_rd = set(lbaas_rds) - set(bigip_rds)
                    for rd_idx in missing_rd:
                        rd = lbaas_rds[rd_idx]
                        tmp = copy.deepcopy(rd)
                        tmp["resource type"] = "route domain"
                        missing.append(tmp)
                        # if project_id not in missing:
                            # missing[project_id] = {rd: lbaas_rds[rd]}
                        # else:
                            # missing[project_id].update({rd: lbaas_rds[rd]})
        return missing

    def get_missing_vlan(self):
        # missing = dict()
        missing = list()
        if self.project_nets:
            subject_vlans = self.get_project_vlans()
            missing = self._find_missing_res(self.project_nets,
                                             subject_vlans)
        return missing


    # check neutron selfip port
    def get_missing_selfip_port(self):

        missing_port = list()
        missing_selfip = list()

        checked = set() 

        # benchmark is neutron db
        for project in self.benchmark_projects:

            bigip_selfips = list()
            try:
                bigip_selfips = self.subject.get_project_selfips(project)
            except iControlUnexpectedHTTPError as ex:
                if ex.response.status_code != 400:
                    raise ex
                    
            bigip_selfips_name = [ip.name for ip in bigip_selfips] 

            lb_resources = list()
            lb_resources = self.benchmark.get_agent_project_loadbalancers(
                project
            )

            # subject is bigip device
            prefix = "local-" + self.subject.device_name + "-"

            for lb in lb_resources:
                if lb.subnet_id in checked:
                    continue

                checked.add(lb.subnet_id) 
                port_name = prefix + lb.subnet_id

                # check if port on device_name bigip
                if port_name not in bigip_selfips_name:
                    missing_selfip.append(port_name)

                # check if port in neutron db
                port = self.benchmark.get_selfip_port(port_name)
                if not port:
                    lb = lb.__dict__

                    # for convert to json file
                    if '_sa_instance_state' in lb:
                        lb.pop('_sa_instance_state')

                    missing_port.append({port_name: lb}) 

        return missing_port, missing_selfip
