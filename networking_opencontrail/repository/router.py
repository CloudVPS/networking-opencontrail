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
from networking_opencontrail.repository.utils.tag import ml2_tag_manager
from networking_opencontrail.repository.utils.utils import request_project

from networking_opencontrail import resources


LOG = logging.getLogger(__name__)


@reconnect
def create(q_router):
    project = request_project(q_router)
    router = resources.router.create(q_router, project)

    ml2_tag_manager.tag(router)

    tf_client.create_logical_router(router)
    LOG.info('Logical Router %s created in TF.', router.get_uuid())


@reconnect
def delete(router_id):
    router = tf_client.read_logical_router(router_id)

    if router is None:
        return

    if not ml2_tag_manager.check(router):
        LOG.debug('Logical Router %s has no ML2 tag - skipping.', router_id)
        return

    tf_client.delete_logical_router(uuid=router_id)
    LOG.info('Logical Router %s deleted from TF.', router_id)
