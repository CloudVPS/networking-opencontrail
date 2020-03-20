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
from networking_opencontrail.repository.utils.tag import ml2_tag_manager
from networking_opencontrail.repository.utils import utils
from networking_opencontrail import resources


LOG = logging.getLogger(__name__)


def create(q_port, q_network):
    try:
        resources.vmi.validate(q_port, q_network)
    except ValueError as e:
        LOG.debug("Did not create a VPG for port %s", q_port["id"])
        LOG.debug(e)
        return

    node = utils.request_node(q_port)
    project = utils.request_project(q_port)

    vpg = _read_vpg(node, project)
    if vpg:
        LOG.info("VPG for port %s already exists", q_port["id"])
        return

    _create_vpg(node, project)


def delete(q_port, q_network):
    try:
        resources.vmi.validate(q_port, q_network)
    except ValueError as e:
        LOG.debug("Did not delete a VPG for port %s", q_port["id"])
        LOG.debug(e)
        return

    node = utils.request_node(q_port)
    project = utils.request_project(q_port)

    vpg = _read_vpg(node, project)
    if not vpg:
        LOG.error("Couldn't find VPG for q_port %s", q_port["id"])
        return

    vmi_refs = vpg.get_virtual_machine_interface_refs()
    if vmi_refs:
        LOG.info("%s should exists - skipping", vpg.name)
        return

    if not ml2_tag_manager.check(vpg):
        LOG.info(
            "%s is not tagged with label=__ML2__ tag - skipping", vpg.name)
        return

    tf_client.delete_vpg(uuid=vpg.uuid)


def _read_vpg(node, project):
    vpg_fq_name = resources.vpg.make_fq_name(node, project)
    vpg = tf_client.read_vpg(fq_name=vpg_fq_name)

    return vpg


def _create_vpg(node, project):
    physical_interfaces = utils.request_physical_interfaces_from_node(node)

    vpg = resources.vpg.create(node, physical_interfaces, project)
    ml2_tag_manager.tag(vpg)

    tf_client.create_vpg(vpg)


def _delete_vpg(node, project):
    vpg_fq_name = resources.vpg.make_fq_name(node, project)

    tf_client.delete_vpg(fq_name=vpg_fq_name)
