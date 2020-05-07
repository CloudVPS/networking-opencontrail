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
from vnc_api import vnc_api

from networking_opencontrail.tests import base

from networking_opencontrail.resources.router import create


class RouterResourceTestCase(base.TestCase):
    """Test cases for Neutron router to VNC Logical Router translation."""

    def test_create_from_q_router(self):
        project = vnc_api.Project()
        q_router = {
            'id': '225c154b-f0d2-4f8d-814e-c219355bc0f9',
            'name': 'test-router',
        }

        router = create(q_router, project)

        self.assertEqual(router.uuid, q_router['id'])
        self.assertEqual(router.name, q_router['name'])
        self.assertEqual(router.logical_router_type, 'vxlan-routing')
