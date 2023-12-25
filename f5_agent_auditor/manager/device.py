# -*- coding: utf-8 -*-

from f5_agent_auditor.bigip import BigipResource
from f5_agent_auditor import utils
from f5_openstack_agent.utils.encrypt import decrypt_data

from oslo_log import log as logging
LOG = logging.getLogger(__name__)


class Device(object):

    def __init__(self, device_group={}, device={}, agent={}):

        self.device_group = device_group
        self.device = device
        self.agent = agent
        self.bigip = None

        self.device_name = None
        self.partition_prefix = None
        self.node_vtep_ip = None
        self.masquerade_mac = None

        self.inner_partitions = [
            '/', 'Common', 'Drafts', 'ServiceDiscovery', 'appsvcs'
        ]

        self.partition_pools = []

        self.build_device_conn()

    def set_dev_ptn_cache(self, lbaas_manager, agents_projects_lbs):
        self.dev_ptn_cache = {}
        project_lbs = agents_projects_lbs.values()
        tenants = self.dev_partitions()
        self.dev_ptn_cache["tenants"] = tenants

        for agent_id, project_lbs in agents_projects_lbs.items():

            agent = lbaas_manager.agents[agent_id]
            agent_config = agent.get("configurations", {})
            env_prefix = agent_config.get("environment_prefix")

            if not env_prefix:
                raise Exception(
                    "Can not find environment_prefix in agent %s" % agent
                )

            for pjt in project_lbs.keys():
                partition = utils.partition_name(
                    env_prefix, pjt
                )

                if partition not in tenants:
                    continue

                if partition not in self.dev_ptn_cache:

                    vlans = self.bigip.get_partition_vlans(partition)
                    vlans = [vlan.name for vlan in vlans]

                    selfips = self.bigip.get_partition_selfips(partition)
                    selfips = [selfip.name for selfip in selfips]

                    rds = self.bigip.get_partition_rds(partition)
                    rds = [rd.name for rd in rds]

                    gws = self.bigip.get_partition_gateways(partition)
                    gws = [gw.name for gw in gws]

                    snatpools = self.bigip.get_partition_snatpools(partition)
                    snatpools = [snatpool.name for snatpool in snatpools]

                    vips = self.bigip.get_partition_vips(partition)
                    vips = [vip.name for vip in vips]

                    vss = self.bigip.get_partition_vss(partition)
                    vss = [vs.name for vs in vss]

                    sys_prefix = ('_sys_', 'bwc_irule', 'acl_irule')
                    rules = self.bigip.get_partition_irules(partition)
                    rules = [rule.name for rule in rules
                             if not rule.name.startswith(sys_prefix)]

                    pool_objs = self.bigip.get_partition_pools(partition)
                    pools = [pl.name for pl in pool_objs]

                    members = self.dev_partition_members(pool_objs)

                    monitors = self.bigip.get_partition_monitors(partition)
                    monitors = [mn.name for mn in monitors]

                    self.dev_ptn_cache[partition] = {
                        "vlans": vlans,
                        "selfips": selfips,
                        "rds": rds,
                        "gateways": gws,
                        "snatpools": snatpools,
                        "vips": vips,
                        "vss": vss,
                        "irules": rules,
                        "pools": pools,
                        "members": members,
                        "monitors": monitors
                    }

    def clean_dev_ptn_cache(self):
        self.dev_ptn_cache = {}

    def set_dev_ptn_pools_cache(self, pools):
        self.partition_pools = pools

    def get_dev_ptn_pools_cache(self):
        return self.partition_pools

    def clean_dev_ptn_pools_cache(self):
        self.partition_pools = []

    def build_device_conn(self):

        v4host = self.device["mgmt_ipv4"]
        device_info = self.device["device_info"]

        serial_number = device_info["serial_number"]
        encrypted_username = device_info["username"]
        encrypted_password = device_info["password"]
        port = device_info["port"]

        self.bigip = BigipResource(
            v4host,
            decrypt_data(serial_number, encrypted_username),
            decrypt_data(serial_number, encrypted_password),
            port=port,
            # token=token
        )

        self.device_name = device_info["device_name"]

    def set_device_config(self, agent):

        self.agent = agent

        # clear all previous settings.
        self.partition_prefix = None
        self.node_vtep_ip = None
        self.masquerade_mac = None

        if not self.bigip:
            raise Exception("Build connection first, "
                            "then set device config")

        agent_config = self.agent.get("configurations", {})
        device_group_config = self.device_group.get("device_info", {})

        env_prefix = agent_config.get("environment_prefix")
        if not env_prefix:
            raise Exception(
                "Can not find environment_prefix in agent %s" % self.agent
            )
        self.partition_prefix = env_prefix

        local_link_info = device_group_config.get("local_link_information", [])
        if not local_link_info:
            raise Exception(
                "Can not find local_link_info in agent %s" % self.agent
            )
        else:
            vtep_ip = local_link_info[0].get("node_vtep_ip")
            if not vtep_ip:
                raise Exception(
                    "Can not find vtep_ip in local_link_info of agent %s" %
                    self.agent
                )
            self.node_vtep_ip = vtep_ip

        masquerade_mac = device_group_config.get("masquerade_mac")
        if not masquerade_mac:
            raise Exception(
                "Can not find querade_mac in agent %s" %
                self.agent
            )
        self.masquerade_mac = masquerade_mac

    def dev_partitions(self):
        partitions = self.bigip.get_partitions()
        partition_names = [p.name for p in partitions]

        ret = [
            part for part in partition_names
            if part not in self.inner_partitions
        ]
        return ret

    def dev_partition_vlans(self, partition):
        # TODO(pzhang) may be set ret as None for telling error happened

        vlans = self.bigip.get_partition_vlans(partition)
        ret = [vlan.name for vlan in vlans]

        return ret

    def dev_partition_rds(self, partition):
        # TODO(pzhang) may be set ret as None for telling error happened

        rds = self.bigip.get_partition_rds(partition)
        ret = [rd.name for rd in rds]

        return ret

    def dev_partition_gateways(self, partition):
        # TODO(pzhang) may be set ret as None for telling error happened

        gws = self.bigip.get_partition_gateways(partition)
        ret = [gw.name for gw in gws]

        return ret

    def dev_partition_selfips(self, partition):
        # TODO(pzhang) may be set ret as None for telling error happened

        selfips = self.bigip.get_partition_selfips(partition)
        ret = [selfip.name for selfip in selfips]

        return ret

    def dev_partition_snatpools(self, partition):

        snatpools = self.bigip.get_partition_snatpools(partition)
        ret = [snatpool.name for snatpool in snatpools]

        return ret

    def dev_partition_vips(self, partition):

        vips = self.bigip.get_partition_vips(partition)
        ret = [vip.name for vip in vips]

        return ret

    def dev_partition_vss(self, partition):

        vss = self.bigip.get_partition_vss(partition)
        ret = [vs.name for vs in vss]

        return ret

    def get_pools(self, partition):

        ret = self.bigip.get_partition_pools(partition)

        return ret

    def dev_partition_pools(self, pools):
        return [pl.name for pl in pools]

    def dev_partition_members(self, pools):
        ret = []
        for pl in pools:
            mbs = pl.members_s.get_collection()
            ret += [mb.description for mb in mbs]
        return ret

    def dev_partition_monitors(self, partition):
        ret = []

        mns = self.bigip.get_partition_monitors(partition)
        ret = [mn.name for mn in mns]

        return ret

    def dev_partition_irules(self, partition):
        sys_prefix = "_sys_"

        rules = self.bigip.get_partition_irules(partition)
        ret = [rule.name for rule in rules
               if not rule.name.startswith(sys_prefix)]

        return ret

    def save_scf(
        self,
        filename="default_auditor.scf",
        directory="/tmp/",
        passphrase=None
    ):
        # diectory: tmsh list sys global-settings
        # file-whitelist-path-prefix file-blacklist-path-prefix
        # file-blacklist-read-only-path-prefix
        if directory:
            filename = directory + filename

        if passphrase:
            options = [
                {
                    "file": filename,
                    "passphrase": passphrase
                }
            ]
        else:
            options = [
                {
                    "file": filename,
                    "no-passphrase": ""
                }
            ]

        self.bigip.config_scf("save", options)

        return filename

    def download_scf(self, src, dst="/tmp/default_auditor.scf"):

        if not src:
            raise Exception(
                "Cannot find src %s to download file" % src)

        self.bigip.download_file(src, dst)

    def mvto_bulk(self, src, dst="/var/config/rest/bulk/"):

        cmd = "-c 'mv " + src + " " + dst + "'"
        self.bigip.run_bash(cmd)
