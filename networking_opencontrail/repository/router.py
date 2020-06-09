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

from networking_opencontrail.repository.utils.client import tf_client
from networking_opencontrail.repository.utils.initialize import reconnect
from networking_opencontrail.repository.utils.irb import \
    select_physical_routers_for_irb
from networking_opencontrail.repository.utils import tagger
from networking_opencontrail.repository.utils.utils import request_project

from networking_opencontrail import resources


LOG = logging.getLogger(__name__)


@reconnect
def create(q_router):
    project = request_project(q_router)
    router = resources.router.create(q_router, project)

    attach_physical_routers(router)

    tf_client.create_logical_router(router)
    LOG.info('Logical Router %s created in TF.', router.get_uuid())


@reconnect
def delete(router_id):
    router = tf_client.read_logical_router(router_id)

    if router is None:
        LOG.info("Logical Router %s does not exist", router_id)
        return

    if not tagger.belongs_to_ntf(router):
        LOG.info("%s was not created by NTF - skipping", router.name)
        return

    tf_client.delete_logical_router(uuid=router_id)
    LOG.info('Logical Router %s deleted from TF.', router.name)


@reconnect
def add_interface(q_router, q_port):
    project = request_project(q_port)

    router = tf_client.read_logical_router(q_router['id'])
    if not router:
        LOG.warning(
            'Could not create router interface %s - router %s not found',
            q_port['id'],
            q_router['id']
        )
        return

    network = tf_client.read_network(q_port['network_id'])
    if not network:
        LOG.warning(
            'Could not create router interface %s - network %s not found',
            q_port['id'],
            q_port['network_id']
        )
        return

    lr_vmi = resources.lr_vmi.create(
        q_port['id'], project, network, router.name)
    lr_vmi.set_virtual_network(network)

    tf_client.create_vmi(lr_vmi)
    LOG.info('VMI for router interface %s created in TF.', lr_vmi.get_uuid())

    router.set_virtual_machine_interface(lr_vmi)
    tf_client.update_logical_router(router)
    LOG.info('VMI %s (%s) attached to Logical Router %s',
             lr_vmi.get_uuid(), network.get_uuid(), router.get_uuid())


@reconnect
def remove_interface(router_id, q_port):
    router = tf_client.read_logical_router(router_id)
    if not router:
        LOG.warning(
            'Could not delete router interface %s - router %s not found',
            q_port['id'],
            router_id
        )
        return

    lr_vmi = tf_client.read_vmi(uuid=q_port['id'])

    if not lr_vmi:
        LOG.debug('Could not delete VMI %s - not found', q_port['id'])
        return

    if not tagger.belongs_to_ntf(lr_vmi):
        LOG.debug(
            'VMI %s doesn not belong to NTF - skipping.', lr_vmi.get_uuid())
        return

    router.del_virtual_machine_interface(lr_vmi)
    tf_client.update_logical_router(router)
    LOG.info('VMI %s removed from Logical Router %s',
             lr_vmi.get_uuid(), router.get_uuid())

    tf_client.delete_vmi(uuid=lr_vmi.uuid)
    LOG.info('VMI for router interface %s deleted from TF.', lr_vmi.get_uuid())


def attach_physical_routers(router):
    all_physical_routers = tf_client.list_physical_routers()
    physical_routers = select_physical_routers_for_irb(all_physical_routers)
    for physical_router in physical_routers:
        router.add_physical_router(physical_router)
