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

class Collector(object):

    def __init__(self, source):
        self.source = source

    def get_project_loadbalancers(project_id, *args, **kwargs):
        """Get loadbalancers by a project_id.

        """
        pass

    def get_project_listeners(project_id, *args, **kwargs):
        """Get listeners by a project_id.

        """
        pass

    def get_project_pools(project_id, *args, **kwargs):
        """Get pools by a project_id.

        """
        pass

    def get_project_members(project_id, *args, **kwargs):
        """Get members by a project_id.

        """
        pass

    def get_project_healthmonitor(project_id, *args, **kwargs):
        """Get healthmonitor by a project_id.

        """
        pass
