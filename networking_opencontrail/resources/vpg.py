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

from networking_opencontrail.common import utils
from oslo_log import log as logging
from vnc_api import vnc_api


LOG = logging.getLogger(__name__)


def create(node, physical_interfaces, fabric):
    name = make_name(node.name)
    id_perms = vnc_api.IdPermsType(enable=True)
    vpg = vnc_api.VirtualPortGroup(
        name=name, parent_obj=fabric, id_perms=id_perms)

    vpg_uuid = utils.make_uuid(vpg.name)
    vpg.set_uuid(vpg_uuid)

    for physical_interface in physical_interfaces:
        vpg.add_physical_interface(ref_obj=physical_interface)

    return vpg


def make_name(node_name):
    return 'vpg#{}'.format(node_name)
