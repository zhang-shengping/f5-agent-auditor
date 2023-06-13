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

from f5_agent_auditor.collector import factory
from f5_agent_auditor import comparator
from f5_agent_auditor.filters import BigIPFilter
from f5_agent_auditor.filters import LbaasFilter
from f5_agent_auditor import options
from f5_agent_auditor.publishers.csv_publisher import \
    CSVPublisher
from f5_agent_auditor.publishers.json_publisher import \
    FilePublisher
from f5_agent_auditor.utils \
    import time_logger

from oslo_log import log as logging

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


conf = options.cfg.CONF
logging.setup(conf, __name__)
LOG = logging.getLogger(__name__)


@time_logger(LOG)
def main():

    LOG.info("Start auditing")
    if conf.f5_agent:
        bigip_filter = BigIPFilter(conf.environment_prefix)
        lbaas_filter = LbaasFilter()

        lbaas_collector = factory.get_collectors("lbaas", conf)[0]
        bigip_collectors = factory.get_collectors("bigip", conf)

        comp = comparator.NetworkLbaasToBigIP(
            lbaas_collector, lbaas_filter
        )

        for collector in bigip_collectors:
            comp.compare_to(collector, bigip_filter)

            # only check vlan, selfip, route of lbs (L3)
            if conf.net == "L2":
                missing_port = list()
                missing_selfip = list()
                missing_port, missing_selfip = comp.get_missing_selfip_port()

                if missing_port:
                    hostname = collector.keys()[0]
                    name = hostname + "_NEUTRON-PORT"

                    file_publisher = FilePublisher(name)
                    file_publisher.publish(missing_port)

                if missing_selfip:
                    hostname = collector.keys()[0]
                    name = hostname + "_BIGIP-PORT"

                    file_publisher = FilePublisher(name)
                    file_publisher.publish(missing_selfip)
              
            missing = list()
            missing += comp.get_missing_projects()
            missing += comp.get_missing_loadbalancers()
            missing += comp.get_missing_listeners()
            missing += comp.get_missing_pools()
            missing += comp.get_missing_members()

            # only check vlan, selfip, route of lbs (L3)
            if conf.net == "L3":
                missing += comp.get_missing_selfip()
                missing += comp.get_missing_route()
                missing += comp.get_missing_route_domain()
                missing += comp.get_missing_vlan()

            if missing:
                csv_publisher = CSVPublisher()
                hostname = collector.keys()[0]
                csv_publisher.set_filepath(hostname)
                csv_publisher.set_csv_fields(
                    "resource type", "uuid",
                    "provisioning status", "project id",
                    "pool id", "detail"
                )
                csv_publisher.publish(*missing)

    else:
        raise Exception("Provide an corresponding agent ID "
                        "--f5-agent")
    LOG.info("Finish auditing")


if __name__ == "__main__":
    main()
