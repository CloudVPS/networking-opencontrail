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
from networking_opencontrail.tests import base

from vnc_api import vnc_api

from networking_opencontrail.resources.lr_vmi import create


class LRVMIResourceTestCase(base.TestCase):
    """Test cases for Neutron router interface to VNC VMI translation."""

    def test_create(self):
        project = vnc_api.Project(name='test-project')
        network = vnc_api.VirtualNetwork(name='test-net', parent_obj=project)
        network.set_uuid('test-net-id')
        router_name = 'test-router'
        port_id = 'port-uuid'

        vmi = create(port_id, project, network, router_name)

        self.assertEqual(vmi.name, 'vmi#test-net#test-router')
        self.assertEqual(vmi.uuid, 'port-uuid')
        self.assertEqual(vmi.parent_name, project.name)
        self.assertEqual(len(vmi.virtual_network_refs), 1)
        self.assertEqual(vmi.virtual_network_refs[0]['uuid'], 'test-net-id')
