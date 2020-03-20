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

import uuid

from neutron_lib.plugins import directory

from networking_opencontrail.common import utils
from networking_opencontrail.repository.client import tf_client
from networking_opencontrail.repository.tag import ml2_tag_manager
from networking_opencontrail.repository.utils import fetch_project
from networking_opencontrail import resources

LOG = logging.getLogger(__name__)


REQUIRED_PORT_FIELDS = [
    'binding:host_id',
    'device_owner',
    'network_id',
]


def create(port, network):
    try:
        resources.vmi.validate(port, network)
    except ValueError as e:
        LOG.debug("Did not create a VMI for port %s", port["id"])
        LOG.debug(e)
        return

    if vmi_exists(port, network):
        LOG.info("VMI for port %s already exists", port["id"])
        return

    project = fetch_project(network)
    tf_network = tf_client.read_network(network["id"])
    vlan_id = network.get("provider:segmentation_id")

    vmi = resources.vmi.create(port, tf_network, project, vlan_id)

    ml2_tag_manager.tag(vmi)

    tf_client.create_vmi(vmi)

    host_id = port["binding:host_id"]
    _attach_to_vpg(vmi, host_id)


def update(port, prev_port, network, context):
    if resources.vmi.needs_update(port, prev_port):
        delete(prev_port, network, context)
        create(port, network)


def delete(port, network, context):
    if _vmi_should_exist(port, network, context):
        return

    vmi_name = resources.vmi.generate_name(port, network)
    vmi_id = utils.generate_uuid(vmi_name)

    vmi = tf_client.read_vmi(vmi_id)
    if not vmi:
        LOG.error("Couldn't find VMI for port %s", port["id"])
        return

    if not ml2_tag_manager.check(vmi):
        LOG.info(
            "%s is not tagged with label=__ML2__ tag - skipping",
            vmi_name
        )
        return

    _detach_from_vpg(vmi)
    tf_client.delete_vmi(vmi.uuid)


def vmi_exists(port, network):
    vmi_name = resources.vmi.generate_name(port, network)
    vmi_uuid = utils.generate_uuid(vmi_name)
    vmi = tf_client.read_vmi(vmi_uuid)
    return bool(vmi)


def _attach_to_vpg(vmi, host_id):
    vpg_name = "vpg_{}".format(host_id)
    vpg_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, vpg_name))
    vpg = tf_client.read_vpg(vpg_uuid)
    vpg.add_virtual_machine_interface(vmi)
    tf_client.update_vpg(vpg)


def _detach_from_vpg(vmi):
    vpg_refs = vmi.get_virtual_port_group_back_refs()
    if not vpg_refs:
        return
    vpg = tf_client.read_vpg(vpg_refs[0]['uuid'])
    vpg.del_virtual_machine_interface(vmi)
    tf_client.update_vpg(vpg)


def _is_managed_by_tf(port, network):
    try:
        resources.vmi.validate(port, network)
    except ValueError:
        return False
    return True


def _vmi_should_exist(port, network, context):
    vmi_ports = directory.get_plugin().get_ports(
        context, filters={'network_id': [network["id"]],
                          'binding:host_id': [port['binding:host_id']]}
    )

    return any(_is_managed_by_tf(vmi_port, network)
               for vmi_port in vmi_ports)
