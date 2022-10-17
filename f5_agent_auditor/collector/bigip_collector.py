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

from f5.bigip import ManagementRoot
from f5_agent_auditor.collector import base
from f5_agent_auditor import resource_helper
from f5_agent_auditor.utils import time_logger
from oslo_log import log as logging

LOG = logging.getLogger(__name__)


class BigIPSource(object):
    def __init__(self, hostname,
                 icontrol_username,
                 icontrol_password):
        self.__hostname = hostname
        self.__icontrol_username = icontrol_username
        self.__icontrol_password = icontrol_password

        self.connection = self.init_bigip()

    @property
    def hostname(self):
        return self.__hostname

    @property
    def username(self):
        return self.__icontrol_username

    @property
    def password(self):
        return None

    def init_bigip(self):
        bigip = ManagementRoot(self.__hostname,
                               self.__icontrol_username,
                               self.__icontrol_password)
        return bigip


class BigIPCollector(base.Collector):
    def __init__(self, source, service_adapter):
        self.bigip = source
        self.service_adapter = service_adapter
        self.device_name = self.get_device_name()

        self.partition_helper = resource_helper.BigIPResourceHelper(
            resource_helper.ResourceType.partition)
        self.vip_helper = resource_helper.BigIPResourceHelper(
            resource_helper.ResourceType.virtual_address)
        self.vs_helper = resource_helper.BigIPResourceHelper(
            resource_helper.ResourceType.virtual)
        self.pool_helper = resource_helper.BigIPResourceHelper(
            resource_helper.ResourceType.pool)
        self.selfip_helper = resource_helper.BigIPResourceHelper(
            resource_helper.ResourceType.selfip)
        self.vlan_helper = resource_helper.BigIPResourceHelper(
            resource_helper.ResourceType.vlan)
        self.rd_helper = resource_helper.BigIPResourceHelper(
            resource_helper.ResourceType.route_domain)
        self.route_helper = resource_helper.BigIPResourceHelper(
            resource_helper.ResourceType.route)

    @staticmethod
    def convert_member_name(bigip_member_name):
        # remove the routedomain id
        if "%" in bigip_member_name:
            port = bigip_member_name.split(":")[1]
            address = bigip_member_name.split("%")[0]
            bigip_member_name = address + ":" + port

        return bigip_member_name

    def get_device_name(self):
        devices = self.bigip.tm.cm.devices.get_collection()
        for dev in devices:
            if dev.selfDevice == 'true':
                return dev.name
        return ""

    @time_logger(LOG)
    def get_projects_on_device(self):
        LOG.info("Get projects on device %s", self.bigip.hostname)
        partitions = self.partition_helper.get_resources(self.bigip)
        return partitions

    @time_logger(LOG)
    def get_project_loadbalancers(self, project_id):
        LOG.info("Get loadbalancers of project: %s", project_id)
        folder_name = self.service_adapter.get_folder_name(project_id)
        loadbalancers = self.vip_helper.get_resources(self.bigip, folder_name)
        return loadbalancers

    @time_logger(LOG)
    def get_project_listeners(self, project_id):
        LOG.info("Get listeners of project: %s", project_id)
        folder_name = self.service_adapter.get_folder_name(project_id)
        listeners = self.vs_helper.get_resources(self.bigip, folder_name)
        return listeners

    @time_logger(LOG)
    def get_project_pools(self, project_id):
        LOG.info("Get pools of project: %s", project_id)
        folder_name = self.service_adapter.get_folder_name(project_id)
        pools = self.pool_helper.get_resources(self.bigip, folder_name, True)
        return pools

    @time_logger(LOG)
    def get_project_selfips(self, project_id):
        LOG.info("Get selfips of project: %s", project_id)
        folder_name = self.service_adapter.get_folder_name(project_id)
        selfips = self.selfip_helper.get_resources(self.bigip, folder_name, True)
        return selfips

    @time_logger(LOG)
    def get_project_vlans(self, project_id):
        LOG.info("Get vlans of project: %s", project_id)
        folder_name = self.service_adapter.get_folder_name(project_id)
        vlans = self.vlan_helper.get_resources(self.bigip, folder_name, True)
        return vlans

    @time_logger(LOG)
    def get_project_rds(self, project_id):
        LOG.info("Get route domain ids of project: %s", project_id)
        folder_name = self.service_adapter.get_folder_name(project_id)
        route_domains = self.rd_helper.get_resources(self.bigip, folder_name, True)
        return route_domains

    @time_logger(LOG)
    def get_project_routes(self, project_id):
        LOG.info("Get routes of project: %s", project_id)
        folder_name = self.service_adapter.get_folder_name(project_id)
        routes = self.route_helper.get_resources(self.bigip, folder_name, True)
        return routes
