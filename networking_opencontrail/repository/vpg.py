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

from networking_opencontrail.repository.utils.client import tf_client
from networking_opencontrail.repository.utils.initialize import reconnect
from networking_opencontrail.repository.utils import tagger
from networking_opencontrail.repository.utils import utils
from networking_opencontrail import resources
from networking_opencontrail.resources.utils import make_uuid


LOG = logging.getLogger(__name__)

PHYSICAL_NETWORK = 'provider:physical_network'


@reconnect
def create(q_port, q_network):
    try:
        resources.vmi.validate(q_port, q_network)
    except ValueError as e:
        LOG.debug("Did not create a VPG for port %s", q_port["id"])
        LOG.debug(e)
        return

    node = utils.request_node(q_port['binding:host_id'])

    if resources.utils.is_sriov_node(node):
        physical_network = q_network[PHYSICAL_NETWORK]
        vpg = create_for_physical_network(node, physical_network)

        return vpg

    vpg = create_for_node(node)

    return vpg


@reconnect
def delete(q_port, q_network):
    try:
        resources.vmi.validate(q_port, q_network)
    except ValueError as e:
        LOG.debug("Did not delete a VPG for port %s", q_port["id"])
        LOG.debug(e)
        return

    node = utils.request_node(q_port['binding:host_id'])
    if resources.utils.is_sriov_node(node):
        physical_network = q_network[PHYSICAL_NETWORK]
        vpg = _read_from_node_and_network(node, physical_network)
    else:
        vpg = _read_from_node(node)

    if not vpg:
        LOG.error("Couldn't find VPG for q_port %s", q_port["id"])
        return

    vmi_refs = vpg.get_virtual_machine_interface_refs()
    if vmi_refs:
        LOG.info("%s should exists - skipping", vpg.name)
        return

    if not tagger.belongs_to_ntf(vpg):
        LOG.info("%s was not created by NTF - skipping", vpg.name)
        return

    tf_client.delete_vpg(uuid=vpg.uuid)


def _read_from_node(node):
    """Read VPG from node"""
    vpg_name = resources.vpg.make_name(node.name)
    vpg_uuid = make_uuid(vpg_name)
    vpg = tf_client.read_vpg(uuid=vpg_uuid)

    return vpg


def _read_from_node_and_network(node, network_name):
    """Read VPG from node and network."""
    vpg_name = resources.vpg.make_name(node.name, network_name)
    vpg_uuid = make_uuid(vpg_name)
    vpg = tf_client.read_vpg(uuid=vpg_uuid)

    return vpg


@reconnect
def create_for_node(node):
    """Create a VPG attached to the provided node."""
    vpg = _read_from_node(node)

    if vpg:
        LOG.info("VPG %s already exists", vpg.display_name)
        return vpg

    fabric = utils.request_fabric_from_node(node)
    if not fabric:
        raise Exception("Couldn't find fabric for VPG")

    vpg = resources.vpg.create(node, fabric)
    tf_client.create_vpg(vpg)

    _add_physical_interfaces(vpg, node)
    tf_client.update_vpg(vpg)

    return vpg


@reconnect
def create_for_physical_network(node, network_name):
    """Create a VPG attached to the provided node and physical network."""
    vpg = _read_from_node_and_network(node, network_name)

    if vpg:
        LOG.info("VPG %s already exists", vpg.display_name)
        return vpg

    fabric = utils.request_fabric_from_node(node)
    if not fabric:
        raise Exception("Couldn't find fabric for VPG")

    vpg = resources.vpg.create(node, fabric, network_name)
    tf_client.create_vpg(vpg)

    _add_physical_interfaces(vpg, node, network_name)
    tf_client.update_vpg(vpg)

    return vpg


def _add_physical_interfaces(vpg, node, network_name=None):
    physical_interfaces = utils.request_physical_interfaces_from_node(
        node, network_name)

    for physical_interface in physical_interfaces:
        vpg.add_physical_interface(ref_obj=physical_interface)
