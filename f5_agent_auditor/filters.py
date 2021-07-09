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

class BigIPFilter(object):

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

    @staticmethod
    def format_member(member):
        address = None
        port = None
        mb = member.get('name')

        if "%" in mb:
            mb = mb.split("%")
            address = mb[0]
            if "." in mb[1]:
                port = mb[1].split('.')[1]
            else:
                port = mb[1].split(":")[1]
        else:
            if mb.count(":") > mb.count("."):
                mb = mb.split('.')
            else:
                mb = mb.split(':')
            address = mb[0]
            port = mb[1]
        address_port = address + "_" + str(port)
        return address_port

    def filter_pool_members(self, partition_pools):
        pools = {}
        for pl in partition_pools:
            members = []
            pl_id = None
            member_items = pl.membersReference.get('items')
            if member_items:
                for mb in member_items:
                    member = self.format_member(mb)
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
        mb['address_port'] = member.address + "_" + str(member.protocol_port)
        mb['id'] = member.id
        mb['provisioning_status'] = member.provisioning_status
        mb['project_id'] = member.project_id
        return mb

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

    def convert_members(self, pool_id, members):
        mbs = [{
            "resource type": "member",
            "uuid": m['id'],
            "provisioning status": m['provisioning_status'],
            "project id": m["project_id"],
            "pool id": pool_id,
            "detail": {
                "address": m['address_port'].split("_")[0],
                "port": m['address_port'].split("_")[1]
            }
        } for m in members]

        return mbs
