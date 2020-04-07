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
from networking_opencontrail.resources.utils import first


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


def unzip_name(vmi_name):
    _, network_uuid, node_name = vmi_name.split('#')
    return network_uuid, node_name


def make_names_from_q_data(q_ports, q_networks):
    """Creates VMI names based on data from neutron.

    For each port, a network that it's connected to is found. Then, based on
    a node the port is bound to, a node-VN pair is used to determine the name
    of the VMI. The process is repeated until names for all VMIs are created.

    One VMI name corresponds to one node-VN pair. Node represents a host on
    which any number of ports that are connected to the given VN exists.
    Example:
    There are two nodes (node-1, node-2) with two ports on each node. One port
    on each node is connected to vn-1 and the other is connected to vn-2.
    To provide connectivity between the ports, four VMIs (one for each node-VN
    pair) must be created. Their names will be:
    vmi#<vn-1-uuid>#node-1
    vmi#<vn-1-uuid>#node-2
    vmi#<vn-2-uuid>#node-1
    vmi#<vn-2-uuid>#node-2

    :param q_ports: list of Neutron ports
    :type q_ports: list
    :param q_networks: list of Neutron networks
    :type q_networks: list
    :return: set of VMI names
    :rtype: set
    """
    vmi_names = set()
    for q_port in q_ports:
        q_port_network_uuid = q_port.get('network_id')
        if not q_port_network_uuid:
            continue

        q_network = first(
            q_networks, lambda q_net: q_net['id'] == q_port_network_uuid)
        if q_network:
            try:
                validate(q_port, q_network)
            except ValueError:
                continue

            q_port_network_uuid = q_network['id']
            node_name = q_port['binding:host_id']
            vmi_name = make_name(q_port_network_uuid, node_name)
            vmi_names.add(vmi_name)

    return vmi_names
