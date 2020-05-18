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

from oslo_log import log as logging
from vnc_api import vnc_api

from networking_opencontrail.repository.utils.client import tf_client
from networking_opencontrail.repository.utils.initialize import reconnect
from networking_opencontrail.repository.utils.utils import request_project
from networking_opencontrail import resources


LOG = logging.getLogger(__name__)


@reconnect
def create(q_subnet):
    project = request_project(q_subnet)
    network = tf_client.read_network(q_subnet["network_id"])

    subnet = resources.subnet.create(q_subnet=q_subnet)

    ipam_refs = network.get_network_ipam_refs()
    if not ipam_refs:
        ipam = tf_client.read_default_ipam(project)
        vn_subnets = vnc_api.VnSubnetsType([subnet])
        network.add_network_ipam(ipam, vn_subnets)
    else:
        vn_subnets = ipam_refs[0]['attr']
        vn_subnets.ipam_subnets.append(subnet)
        network._pending_field_updates.add('network_ipam_refs')

    tf_client.update_network(network)


@reconnect
def update(q_subnet):
    delete(q_subnet)
    create(q_subnet)


@reconnect
def delete(q_subnet):
    try:
        network = tf_client.read_network(q_subnet["network_id"])
        _delete_from_network(network, q_subnet)
    except KeyError:
        networks = tf_client.list_networks()
        for network in networks:
            _delete_from_network(network, q_subnet)


def _delete_from_network(network, q_subnet):
    ipam_refs = network.get_network_ipam_refs()
    if not ipam_refs:
        return
    vn_subnets = ipam_refs[0]['attr']
    for subnet in list(vn_subnets.ipam_subnets):
        if subnet.subnet_uuid == q_subnet["id"]:
            vn_subnets.ipam_subnets.remove(subnet)

    network._pending_field_updates.add('network_ipam_refs')
    tf_client.update_network(network)