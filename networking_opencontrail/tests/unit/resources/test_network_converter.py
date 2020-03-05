# Copyright (c) 2016 OpenStack Foundation
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

from networking_opencontrail.tests import base
from vnc_api import vnc_api

from networking_opencontrail.resources.network import create
from networking_opencontrail.resources.network import update


class NetworkConverterTestCase(base.TestCase):

    def test_create_from_q_network(self):
        q_network = {
            'id': 'fadffa22-3022-4bdb-9045-0b5de8901d3c',
            'name': u'test_network',
        }
        project = vnc_api.Project(name='project_name')
        network = create(q_network=q_network, project=project)

        self.assertEqual(network.uuid, q_network['id'])
        self.assertEqual(network.name, q_network['name'])
        self.assertEqual(network.id_perms, vnc_api.IdPermsType(enable=True))

    def test_update_from_q_network(self):
        old_q_network = {
            'id': 'fadffa22-3022-4bdb-9045-0b5de8901d3c',
            'name': u'old_name',
        }

        q_network = old_q_network.copy()
        q_network['name'] = u'new_name'

        project = vnc_api.Project(name='project_name')
        old_network = create(q_network=old_q_network,
                             project=project)

        network = update(old_network=old_network,
                         q_network=q_network)

        self.assertEqual(network.display_name, q_network['name'])
