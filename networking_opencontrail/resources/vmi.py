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


def create(port, tf_network, project, vlan_id):
    name = generate_name(port, tf_network)
    vmi = vnc_api.VirtualMachineInterface(name=name, parent_obj=project)
    vmi.set_uuid(utils.generate_uuid(name))

    id_perms = vnc_api.IdPermsType(enable=True, creator=project.uuid)
    vmi.set_id_perms(id_perms)

    vmi_properties = vnc_api.VirtualMachineInterfacePropertiesType(
        sub_interface_vlan_tag=vlan_id
    )
    vmi.set_virtual_machine_interface_properties(vmi_properties)

    vmi.set_virtual_network(tf_network)

    return vmi


def validate(port, network):
    for field in REQUIRED_PORT_FIELDS:
        if field not in port:
            raise ValueError("No {} field in port".format(field))

    if not port.get("device_owner", "").startswith(
        constants.DEVICE_OWNER_COMPUTE_PREFIX):
        raise ValueError("Invalid device_owner field value")

    if not network.get("provider:segmentation_id"):
        raise ValueError(
            "No VLAN ID set for network {}".format(network["name"]))


def needs_update(port, prev_port):
    for field in REQUIRED_PORT_FIELDS:
        if port.get(field) != prev_port.get(field):
            return True
    return False


def generate_name(port, network):
    try:
        network_name = network.name
    except AttributeError:
        network_name = network["name"]
    host_id = port["binding:host_id"]
    vmi_name = "vmi_{}_{}".format(network_name, host_id)
    return vmi_name
