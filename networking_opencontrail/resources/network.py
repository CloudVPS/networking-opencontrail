# Copyright (c) 2019 OpenStack Foundation
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

from oslo_log import log as logging
from vnc_api import vnc_api


LOG = logging.getLogger(__name__)


def create(q_network, project):
    id_perms = vnc_api.IdPermsType(enable=True)
    network = vnc_api.VirtualNetwork(
        name=q_network['id'],
        display_name=q_network['name'],
        parent_obj=project,
        id_perms=id_perms)

    network.uuid = q_network['id']

    return network
