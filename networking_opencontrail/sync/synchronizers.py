# Copyright (c) 2020 OpenStack Foundation
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#

from networking_opencontrail import repository
from networking_opencontrail.sync.base import ResourceSynchronizer


class NetworkSynchronizer(ResourceSynchronizer):
    LOG_RES_NAME = "Network"

    def _get_tf_resources(self):
        return repository.network.list_all()

    def _get_neutron_resources(self):
        return self._core_plugin.get_networks(self._context)

    def _create_resource(self, resource):
        repository.network.create(resource)

    def _delete_resource(self, resource_id):
        repository.network.delete({"id": resource_id})

    def _ignore_tf_resource(self, resource):
        return (resource.get_fq_name()[1] == "default-project"
                or self._no_ml2_tag(resource))

    def _ignore_neutron_resource(self, resource):
        return "_snat_" in resource["name"]
