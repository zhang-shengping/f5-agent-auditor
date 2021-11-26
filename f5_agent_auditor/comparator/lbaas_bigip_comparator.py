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
