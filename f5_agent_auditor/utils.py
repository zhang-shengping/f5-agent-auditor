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

from distutils.version import LooseVersion
from functools import wraps

import constants
import netaddr
import time
import psutil
import os

collection_map = {
    "nat": lambda bigip: bigip.tm.ltm.nats,
    "pool": lambda bigip: bigip.tm.ltm.pools,
    "sys": lambda bigip: bigip.tm.sys,
    "virtual": lambda bigip: bigip.tm.ltm.virtuals,
    "member": lambda bigip: bigip.tm.ltm.pools.pool.member,
    "folder": lambda bigip: bigip.tm.sys.folders,
    "http_monitor":
        lambda bigip: bigip.tm.ltm.monitor.https,
    "https_monitor":
        lambda bigip: bigip.tm.ltm.monitor.https_s,
    "tcp_monitor":
        lambda bigip: bigip.tm.ltm.monitor.tcps,
    "ping_monitor":
        lambda bigip: bigip.tm.ltm.monitor.gateway_icmps,
    "node": lambda bigip: bigip.tm.ltm.nodes,
    "snat": lambda bigip: bigip.tm.ltm.snats,
    "snatpool":
        lambda bigip: bigip.tm.ltm.snatpools,
    "snat_translation":
        lambda bigip: bigip.tm.ltm.snat_translations,
    "selfip":
        lambda bigip: bigip.tm.net.selfips,
    "rule":
        lambda bigip: bigip.tm.ltm.rules,
    "route_domain":
        lambda bigip: bigip.tm.net.route_domains,
    "route":
        lambda bigip: bigip.tm.net.routes,
    "vlan":
        lambda bigip: bigip.tm.net.vlans,
    "arp":
        lambda bigip: bigip.tm.net.arps,
    "tunnel":
        lambda bigip: bigip.tm.net.tunnels.tunnels,
    "virtual_address":
        lambda bigip: bigip.tm.ltm.virtual_address_s,
    "l7policy":
        lambda bigip: bigip.tm.ltm.policys,
    "client_ssl_profile":
        lambda bigip: bigip.tm.ltm.profile.client_ssls,
    "server_ssl_profile":
        lambda bigip: bigip.tm.ltm.profile.server_ssls,
    "tcp_profile":
        lambda bigip: bigip.tm.ltm.profile.tcps,
    "persistence":
        lambda bigip: bigip.tm.ltm.persistence,
    "cookie_persistence":
        lambda bigip: bigip.tm.ltm.persistence.cookies,
    "dest_addr_persistence":
        lambda bigip: bigip.tm.ltm.persistence.dest_addrs,
    "hash_persistence":
        lambda bigip: bigip.tm.ltm.persistence.hashs,
    "msrdp_persistence":
        lambda bigip: bigip.tm.ltm.persistence.msrdps,
    "sip_persistence":
        lambda bigip: bigip.tm.ltm.persistence.sips,
    "source_addr_persistence":
        lambda bigip: bigip.tm.ltm.persistence.source_addrs,
    "ssl_persistence":
        lambda bigip: bigip.tm.ltm.persistence.ssls,
    "universal_persistence":
        lambda bigip: bigip.tm.ltm.persistence.universals,
    "ssl_cert_file":
        lambda bigip: bigip.tm.sys.file.ssl_certs,
    "http_profile":
        lambda bigip: bigip.tm.ltm.profile.https,
    "http2_profile":
        lambda bigip: bigip.tm.ltm.profile.http2s,
    "oneconnect":
        lambda bigip: bigip.tm.ltm.profile.one_connects,
    "bwc_policy":
        lambda bigip: bigip.tm.net.bwc.policys,
    "websocket_profile":
        lambda bigip: bigip.tm.ltm.profile.websockets,
    "device":
        lambda bigip: bigip.tm.cm.devices,
    "cipher_group":
        lambda bigip: bigip.tm.ltm.cipher.groups,
    "cipher_rule":
        lambda bigip: bigip.tm.ltm.cipher.rules,
}



def time_logger(logger):
    def timer(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            end = time.time()
            elapse = end - start
            logger.info(
                "%s takes %s seconds",
                func.__name__, elapse
            )
            return result
        return wrapper
    return timer


def get_filter(bigip, key, op, value):
    if LooseVersion(bigip.tmos_version) < LooseVersion('11.6.0'):
        return '$filter=%s+%s+%s' % (key, op, value)
    else:
        return {'$filter': '%s %s %s' % (key, op, value)}


def get_vlan_segid(vtep_ip, net):
    ret = None

    segs = net["segments"]
    seg = segs.get(vtep_ip)

    if not seg:
        seg = segs.values()[0]

    net_type = seg.get("network_type")
    if net_type != "vlan":
        raise Exception(
            "Cannot find segment id in network %s" % net
        )
    ret = seg.get("segmentation_id")

    return ret


def partition_name(prefix, project_id):
    return prefix + '_' + project_id


def vlan_name(seg_id):
    return 'vlan-' + str(seg_id)


def rd_name(prefix, net_id):
    return prefix + '_' + net_id


def selfip_name(device_name, subnet_id):
    return 'local-' + device_name + '-' + subnet_id


def gatewy_name(addr, seg_id):
    version = netaddr.IPAddress(addr).version
    seg_id = str(seg_id)
    if version == 4:
        return "IPv4_default_route_" + seg_id
    if version == 6:
        return "IPv6_default_route_" + seg_id


def res_name(prefix, res_id):
    return prefix + '_' + res_id


def remove_prefix(name):
    res_id = name.split("_")[1]
    return res_id


def get_project_ids(partitions):
    return [remove_prefix(name) for name in partitions]


def timestamp_filename(name):
    timestr = time.strftime("%Y%m%d-%H%M%S")
    return name + "_" + timestr


def timestamp_bash(name):
    timestr = time.strftime("%Y%m%d-%H%M%S")
    return name + "_" + timestr + ".sh"


def retry(func):
    def inner(*args, **kwargs):
        times = 3
        while times > 0:
            try:
                ret = func(*args, **kwargs)
                return ret
            except Exception as ex:
                times -= 1
                if times > 0:
                    continue
                else:
                    raise ex
    return inner


def to_dict(bigip_objs, expand_subcollections=False):
    ret = {}

    if expand_subcollections:
        ret = {obj.fullPath: obj.load(
            expand_subcollections=expand_subcollections).attrs
               for obj in bigip_objs}
    else:
        ret = {obj.fullPath: obj.attrs for obj in bigip_objs}

    return ret


# selfip cannot use this, because hostname is always different.
def diff(ac, bp):
    # this function could compare dict, list of dict,
    # nested dict and nested list of dict types.

    ret = {}

    # compare dict type
    if isinstance(ac, dict) and isinstance(bp, dict):
        diff_keys = set(ac.keys()) - set(bp.keys())
        for k in diff_keys:
            if k in constants.EXCLUSIVE_KEYS:
                continue

            ret[k] = {"active": ac.pop(k), "backup": None}

        for k in ac.keys():
            if k in constants.EXCLUSIVE_KEYS:
                continue

            df = diff(ac[k], bp[k])
            if df:
                ret[k] = diff(ac[k], bp[k])
        return ret

    # compare other types
    if ac != bp:
        if isinstance(ac, list) and isinstance(bp, list):

            if _is_dict_list(ac, bp):

                ac, bp = comparable_list(ac, bp)

                if all([ac, bp]):
                    df = diff(ac, bp)
                    return df

        return {"active": ac, "backup": bp}

    return ret


def comparable_list(alist, blist):
    acomparable = None
    bcomparable = None

    try:
        acomparable = {a["name"]: a for a in alist}
        bcomparable = {b["name"]: b for b in blist}
    except Exception:
        return None, None

    return acomparable, bcomparable


def _is_dict_list(ac, bp):
    ac_ret = all([isinstance(v, dict) for v in ac])
    bp_ret = all([isinstance(v, dict) for v in bp])

    return all([ac_ret, bp_ret])


def format_bytes(bytes):
    if abs(bytes) < 1000:
        return str(bytes)+"B"
    elif abs(bytes) < 1e6:
        return str(round(bytes/1e3, 2)) + "kB"
    elif abs(bytes) < 1e9:
        return str(round(bytes / 1e6, 2)) + "MB"
    else:
        return str(round(bytes / 1e9, 2)) + "GB"


def profile(LOG):
    def dec(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            process = psutil.Process(os.getpid())

            start = process.memory_info().rss
            ret = func(*args, **kwargs)
            end = process.memory_info().rss
            func_name = func.__name__
            mem_consume = format_bytes(end - start)

            LOG.info("function %s: consumed: %s", func_name, mem_consume)

            return ret
        return wrapper
    return dec


def split_fullpath(path):

    partition, name = None, None
    splitpath = path.split("/")

    partition = splitpath[1]
    name = splitpath[2]

    return partition, name


def split_partition(ptn):

    prefix, tenant_id = None, None
    splitpath = ptn.split("_")

    prefix = splitpath[0]
    tenant_id = splitpath[1]

    return prefix, tenant_id
