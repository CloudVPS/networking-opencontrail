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
from vnc_api import vnc_api


LOG = logging.getLogger(__name__)
LOGICAL_ROUTER_TYPE = 'vxlan-routing'


def create(q_router, project):
    router_name = q_router['name']
    id_perms = vnc_api.IdPermsType(enable=True)
    logical_router = vnc_api.LogicalRouter(
        name=router_name, parent_obj=project, id_perms=id_perms)
    logical_router.uuid = q_router['id']
    logical_router.set_logical_router_type(LOGICAL_ROUTER_TYPE)

    return logical_router