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

from networking_opencontrail.resources.utils import first
from networking_opencontrail.resources.vmi import validate


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


def unzip_name(vpg_name):
    _, node_name, = vpg_name.split('#')
    return node_name


def make_names_from_q_data(q_ports, q_networks):
    """Creates VPG names based on data from neutron.

    For each port, a network that it's connected to is found. Then, based on
    a node the port is bound to, the name of VPG is created. The process is
    repeated until names for all VMIs are created.

    One VPG name corresponds to a node in which any number of ports that are
    connected to a Virtual Network exists.
    Example:
    There are two nodes (node-1, node-2) with two ports on each node connected
    to a Virtual Network. To provide connectivity between the ports, two VPGs
    (one for each node) must be created. Their names will be:
    vpg#node-1
    vpg#node-2

    :param q_ports: list of Neutron ports
    :type q_ports: list
    :param q_networks: list of Neutron networks
    :type q_networks: list
    :return: set of VPG names
    :rtype: set
    """
    vpg_names = set()
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

            node_name = q_port['binding:host_id']
            vpg_name = make_name(node_name)
            vpg_names.add(vpg_name)

    return vpg_names
