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

from networking_opencontrail.repository.client import tf_client
from networking_opencontrail.repository.initialize import reconnect
from networking_opencontrail.repository.tag import ml2_tag_manager
from networking_opencontrail.repository.utils import fetch_project
from networking_opencontrail import resources


LOG = logging.getLogger(__name__)


@reconnect
def list_all():
    return tf_client.list_networks()


@reconnect
def create(q_network):
    project = fetch_project(q_network)
    network = resources.network.create(q_network=q_network,
                                       project=project)

    ml2_tag_manager.tag(network)

    tf_client.create_network(network)


@reconnect
def update(old_q_network, q_network):
    project = fetch_project(old_q_network)
    old_network = resources.network.create(
        q_network=old_q_network, project=project)
    network = resources.network.update(
        old_network=old_network, q_network=q_network)

    tf_client.update_network(network)


@reconnect
def delete(q_network):
    network_id = q_network['id']

    tf_client.delete_network(network_id=network_id)
