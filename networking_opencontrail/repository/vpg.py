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

from networking_opencontrail.common.utils import make_uuid
from networking_opencontrail.repository.utils.client import tf_client
from networking_opencontrail.repository.utils.initialize import reconnect
from networking_opencontrail.repository.utils import tagger
from networking_opencontrail.repository.utils import utils
from networking_opencontrail import resources


LOG = logging.getLogger(__name__)


@reconnect
def create(q_port, q_network):
    try:
        resources.vmi.validate(q_port, q_network)
    except ValueError as e:
        LOG.debug("Did not create a VPG for port %s", q_port["id"])
        LOG.debug(e)
        return

    node = utils.request_node(q_port)
    vpg = _read_from_node(node)
    if vpg:
        LOG.info("VPG for port %s already exists", q_port["id"])
        return

    vpg = create_from_node(node)
    return vpg


@reconnect
def delete(q_port, q_network):
    try:
        resources.vmi.validate(q_port, q_network)
    except ValueError as e:
        LOG.debug("Did not delete a VPG for port %s", q_port["id"])
        LOG.debug(e)
        return

    node = utils.request_node(q_port)
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
    vpg_name = resources.vpg.make_name(node.name)
    vpg_uuid = make_uuid(vpg_name)
    vpg = tf_client.read_vpg(uuid=vpg_uuid)

    return vpg


@reconnect
def create_from_node(node):
    physical_interfaces = utils.request_physical_interfaces_from_node(node)
    fabric = utils.request_fabric_from_node(node)
    if not fabric:
        LOG.error("Couldn't find fabric for VPG")
        return

    vpg = resources.vpg.create(node, physical_interfaces, fabric)

    tf_client.create_vpg(vpg)
    return vpg


def _delete_vpg(node):
    vpg_name = resources.vpg.make_name(node)
    vpg_uuid = make_uuid(vpg_name)

    tf_client.delete_vpg(uuid=vpg_uuid)
