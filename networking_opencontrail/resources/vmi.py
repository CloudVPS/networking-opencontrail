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
from neutron_lib import constants
from vnc_api import vnc_api

from networking_opencontrail.common import utils

REQUIRED_PORT_FIELDS = [
    "binding:host_id",
    "device_owner",
    "network_id",
]


def create(project, network, node_name, vlan_id):
    name = make_name(network.uuid, node_name)
    vmi = vnc_api.VirtualMachineInterface(name=name, parent_obj=project)
    vmi.set_uuid(utils.make_uuid(name))

    id_perms = vnc_api.IdPermsType(enable=True, creator=project.uuid)
    vmi.set_id_perms(id_perms)

    vmi_properties = vnc_api.VirtualMachineInterfacePropertiesType(
        sub_interface_vlan_tag=vlan_id
    )
    vmi.set_virtual_machine_interface_properties(vmi_properties)

    vmi.set_virtual_network(network)

    return vmi


def validate(q_port, q_network):
    for field in REQUIRED_PORT_FIELDS:
        if field not in q_port:
            raise ValueError("No {} field in port".format(field))

    if not q_port.get("device_owner", "").startswith(
        constants.DEVICE_OWNER_COMPUTE_PREFIX):
        raise ValueError("Invalid device_owner field value")

    if not q_network.get("provider:segmentation_id"):
        raise ValueError(
            "No VLAN ID set for network {}".format(q_network["name"]))


def make_name(network_uuid, node_name):
    vmi_name = "vmi#{}#{}".format(network_uuid, node_name)
    return vmi_name
