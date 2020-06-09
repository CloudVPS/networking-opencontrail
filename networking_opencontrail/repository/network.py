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
from networking_opencontrail.repository.utils.utils import request_project
from networking_opencontrail import resources


LOG = logging.getLogger(__name__)


@reconnect
def list_all():
    return tf_client.list_networks()


@reconnect
def create(q_network):
    project = request_project(q_network)
    network = resources.network.create(
        q_network=q_network, project=project)

    tf_client.create_network(network)


@reconnect
def update(old_q_network, q_network):
    network = tf_client.read_network(old_q_network['id'])
    if not tagger.belongs_to_ntf(network):
        LOG.info("%s was not created by NTF - skipping", network.name)
        return

    network.display_name = q_network['name']

    tf_client.update_network(network)


@reconnect
def delete(q_network):
    network = tf_client.read_network(q_network['id'])

    if network is None:
        LOG.info("Virtual Network %s does not exist", q_network['id'])
        return

    if not tagger.belongs_to_ntf(network):
        LOG.info("%s was not created by NTF - skipping", network.name)
        return

    tf_client.delete_network(uuid=network.uuid)
