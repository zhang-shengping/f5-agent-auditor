# -*- coding: utf-8 -*-

from f5_agent_auditor import utils
from f5.bigip import ManagementRoot


class BigipResource(object):

    def __init__(self, v4host, username, password, port):

        self.bigip = self.conn(
            v4host, username, password, port=port,
            debug=True
        )

    def collection(self, resource_type):
        if resource_type in utils.collection_map:
            return utils.collection_map[resource_type](self.bigip)
        else:
            raise KeyError("No collection available for %s" %
                           (self.resource_type))

    @utils.retry
    def conn(self, v4host, username, password, port, debug=True):
        ret = ManagementRoot(
            v4host, username, password, port=port,
            debug=True
        )

        return ret

    @utils.retry
    def get_partitions(self):
        ret = self.bigip.tm.sys.folders.get_collection()
        return ret

    @utils.retry
    def get_partition_vlans(self, partition):

        params = {'params': ''}
        params['params'] = utils.get_filter(
            self.bigip, 'partition', 'eq', partition
        )

        # NOTE(pzhang) get resources from partition, the arguements
        # is not partition=partition.
        ret = self.bigip.tm.net.vlans.get_collection(
            requests_params=params)

        return ret

    @utils.retry
    def get_partition_rds(self, partition):

        params = {'params': ''}
        params['params'] = utils.get_filter(
            self.bigip, 'partition', 'eq', partition
        )

        ret = self.bigip.tm.net.route_domains.get_collection(
            requests_params=params)

        return ret

    @utils.retry
    def get_partition_gateways(self, partition):

        params = {'params': ''}
        params['params'] = utils.get_filter(
            self.bigip, 'partition', 'eq', partition
        )

        ret = self.bigip.tm.net.routes.get_collection(
            requests_params=params)

        return ret

    @utils.retry
    def get_partition_selfips(self, partition):

        params = {'params': ''}
        params['params'] = utils.get_filter(
            self.bigip, 'partition', 'eq', partition
        )

        ret = self.bigip.tm.net.selfips.get_collection(
            requests_params=params)

        return ret

    @utils.retry
    def get_partition_snatpools(self, partition):

        params = {'params': ''}
        params['params'] = utils.get_filter(
            self.bigip, 'partition', 'eq', partition
        )

        ret = self.bigip.tm.ltm.snatpools.get_collection(
            requests_params=params)

        return ret

    @utils.retry
    def get_partition_vips(self, partition):

        params = {'params': ''}
        params['params'] = utils.get_filter(
            self.bigip, 'partition', 'eq', partition
        )

        ret = self.bigip.tm.ltm.virtual_address_s.get_collection(
            requests_params=params)

        return ret

    @utils.retry
    def get_partition_vss(self, partition):

        params = {'params': ''}
        params['params'] = utils.get_filter(
            self.bigip, 'partition', 'eq', partition
        )

        ret = self.bigip.tm.ltm.virtuals.get_collection(
            requests_params=params)

        return ret

    @utils.retry
    def get_partition_pools(self, partition):
        params = {'params': ''}
        params['params'] = utils.get_filter(
            self.bigip, 'partition', 'eq', partition
        )

        # bigip.tm.ltm.pools.pool.member
        ret = self.bigip.tm.ltm.pools.get_collection(
            requests_params=params)

        # pools[0].members_s.get_collection()
        return ret

    @utils.retry
    def get_partition_monitors(self, partition):

        types = {
            "TCP": self.bigip.tm.ltm.monitor.tcps,
            "HTTP": self.bigip.tm.ltm.monitor.https,
            "HTTPS": self.bigip.tm.ltm.monitor.https_s,
            "UDP": self.bigip.tm.ltm.monitor.udps,
            # "SIP": self.bigip.tm.ltm.monitor.udps,
            # "Diameter": self.bigip.tm.ltm.monitor.diameters,
            "PING":  self.bigip.tm.ltm.monitor.gateway_icmps
        }

        params = {'params': ''}
        params['params'] = utils.get_filter(
            self.bigip, 'partition', 'eq', partition
        )
        ret = []

        for monitor_handler in types.values():
            ret += monitor_handler.get_collection(requests_params=params)

        return ret

    @utils.retry
    def get_partition_irules(self, partition):

        params = {'params': ''}
        params['params'] = utils.get_filter(
            self.bigip, 'partition', 'eq', partition
        )

        ret = []

        ret = self.bigip.tm.ltm.rules.get_collection(
            requests_params=params)

        return ret

    @utils.retry
    def config_scf(self, cmd, options):
        if not cmd:
            cmd = "save"

        ret = self.bigip.tm.sys.config.exec_cmd(
            cmd, options=options
        )
        return ret

    @utils.retry
    def download_file(self, src, dst):

        ret = self.bigip.shared.file_transfer.bulk.download_file(
            src, dst)

        # self.bigip.shared.file_transfer.tmp.download_file(
            # src, dst)

        return ret

    @utils.retry
    def run_bash(self, cmd):

        ret = self.bigip.tm.util.bash.exec_cmd(
            command='run',
            utilCmdArgs=cmd
        )

        return ret

    @utils.retry
    def devices(self):
        return self.bigip.tm.cm.devices.get_collection()

    @utils.retry
    def get_device_info(self, device_name):
        device_info = self.bigip.tm.cm.devices.device.load(
            name=device_name, partition='Common'
        )
        return device_info

    @utils.retry
    def get_vips(self):
        ret = self.bigip.tm.ltm.virtual_address_s.get_collection()
        return ret

    @utils.retry
    def get_vss(self):
        ret = self.bigip.tm.ltm.virtuals.get_collection()
        return ret

    @utils.retry
    def get_pools(self):
        # bigip.tm.ltm.pools.pool.member
        ret = self.bigip.tm.ltm.pools.get_collection()

        # pools[0].members_s.get_collection()
        return ret

    @utils.retry
    def get_monitors(self):

        types = {
            "TCP": self.bigip.tm.ltm.monitor.tcps,
            "HTTP": self.bigip.tm.ltm.monitor.https,
            "HTTPS": self.bigip.tm.ltm.monitor.https_s,
            "UDP": self.bigip.tm.ltm.monitor.udps,
            # "SIP": self.bigip.tm.ltm.monitor.udps,
            # "Diameter": self.bigip.tm.ltm.monitor.diameters,
            "PING":  self.bigip.tm.ltm.monitor.gateway_icmps
        }

        ret = []

        for monitor_handler in types.values():
            ret += monitor_handler.get_collection()

        return ret
