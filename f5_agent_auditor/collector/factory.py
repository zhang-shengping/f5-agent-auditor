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

from f5_agent_auditor.collector import \
    bigip_collector
from f5_agent_auditor.collector import \
    lbaas_collector
from f5_agent_auditor.db import queries
from f5_openstack_agent.lbaasv2.drivers.bigip.service_adapter import \
    ServiceModelAdapter


def get_collectors(collector_type, conf):

    collectors = []
    collector = dict()

    if collector_type == "lbaas":
        db_query = queries.Queries()
        collector['lbaas'] = lbaas_collector.LbassDBCollector(
            db_query, conf.f5_agent)
        collectors.append(collector)

    elif collector_type == "bigip":
        service_adapter = ServiceModelAdapter(conf)
        ips = conf.icontrol_hostname
        hostnames = parse_hostnames(ips)

        for hostname in hostnames:
            source = bigip_collector.BigIPSource(
                hostname, conf.icontrol_username, conf.icontrol_password
            )
            collector[hostname] = bigip_collector.BigIPCollector(
                source.connection,
                service_adapter)
            collectors.append(collector)
            collector = dict()

    else:
        raise Exception("collector type %s is not registered", collector_type)

    return collectors


def parse_hostnames(hostname_str):
    hostnames = hostname_str.split(',')
    hostnames = [item.strip() for item in hostnames]
    return set(hostnames)
