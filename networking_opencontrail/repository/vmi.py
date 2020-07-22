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
import logging

from neutron_lib.plugins import directory

from networking_opencontrail.common import utils
from networking_opencontrail.repository.utils.client import tf_client
from networking_opencontrail.repository.utils.initialize import reconnect
from networking_opencontrail.repository.utils import tagger
from networking_opencontrail.repository.utils.utils import request_project
from networking_opencontrail import resources

LOG = logging.getLogger(__name__)


REQUIRED_PORT_FIELDS = [
    'binding:host_id',
    'device_owner',
    'network_id',
]


@reconnect
def create(q_port, q_network, vpg_name):
    try:
        resources.vmi.validate(q_port, q_network)
    except ValueError as e:
        LOG.debug("Did not create a VMI for port %s", q_port["id"])
        LOG.debug(e)
        return

    project = request_project(q_network)
    node_name = q_port['binding:host_id']
    network_uuid = q_network['id']
    if vmi_exists(network_uuid, node_name):
        LOG.info("VMI for port %s already exists", q_port["id"])
        return

    network = tf_client.read_network(uuid=q_network["id"])
    vlan_id = q_network.get("provider:segmentation_id")
    create_from_tf_data(project, network, node_name, vlan_id, vpg_name)


@reconnect
def delete(q_port, q_network, context):
    try:
        resources.vmi.validate(q_port, q_network)
    except ValueError as e:
        LOG.debug("Did not delete a VMI for port %s", q_port["id"])
        LOG.debug(e)
        return

    network_uuid = q_network['id']
    node_name = q_port['binding:host_id']
    vmi_name = resources.vmi.make_name(network_uuid, node_name)
    if _vmi_should_exist(q_port, q_network, context):
        LOG.info("%s should exists - skipping", vmi_name)
        return

    vmi_id = utils.make_uuid(vmi_name)
    vmi = tf_client.read_vmi(uuid=vmi_id)
    if not vmi:
        LOG.error("Couldn't find VMI for q_port %s", q_port["id"])
        return

    if not tagger.belongs_to_ntf(vmi):
        LOG.info("%s was not created by NTF - skipping", vmi.name)
        return

    detach_from_vpg(vmi)
    tf_client.delete_vmi(uuid=vmi.uuid)


@reconnect
def vmi_exists(network_uuid, node_name):
    vmi_name = resources.vmi.make_name(network_uuid, node_name)
    vmi_uuid = utils.make_uuid(vmi_name)
    vmi = tf_client.read_vmi(uuid=vmi_uuid)

    return bool(vmi)


@reconnect
def create_from_tf_data(project, network, node_name, vlan_id, vpg_name):
    vmi = resources.vmi.create(project, network, node_name, vlan_id)

    tf_client.create_vmi(vmi)

    _attach_to_vpg(vmi, vpg_name)


def _attach_to_vpg(vmi, vpg_name):
    vpg_uuid = utils.make_uuid(vpg_name)

    vpg = tf_client.read_vpg(uuid=vpg_uuid)
    vpg.add_virtual_machine_interface(vmi)
    tf_client.update_vpg(vpg)


def detach_from_vpg(vmi):
    vpg_refs = vmi.get_virtual_port_group_back_refs()
    if not vpg_refs:
        return
    vpg = tf_client.read_vpg(uuid=vpg_refs[0]['uuid'])
    vpg.del_virtual_machine_interface(vmi)
    tf_client.update_vpg(vpg)


def _is_managed_by_tf(q_port, q_network):
    try:
        resources.vmi.validate(q_port, q_network)
    except ValueError:
        return False
    return True


def _vmi_should_exist(q_port, q_network, context):
    vmi_ports = directory.get_plugin().get_ports(context)

    vmi_ports = (
        vmi_port for vmi_port in vmi_ports
        if vmi_port['network_id'] == q_network['id']
        and vmi_port['binding:host_id'] == q_port['binding:host_id']
    )

    return any(_is_managed_by_tf(vmi_port, q_network)
               for vmi_port in vmi_ports)
