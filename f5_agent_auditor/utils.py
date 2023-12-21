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
import netaddr
import time


def time_logger(logger):
    def timer(func):
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
