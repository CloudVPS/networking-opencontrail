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

import uuid

from oslo_log import log as logging

from networking_opencontrail.repository.client import tf_client


LOG = logging.getLogger(__name__)


def fetch_project(q_object):
    project_id = str(uuid.UUID(q_object['tenant_id']))
    project = tf_client.read_project(project_id=project_id)
    return project
