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

from networking_opencontrail.resources.vpg import create
from networking_opencontrail.resources.vpg import make_name
from networking_opencontrail.resources.vpg import unzip_name


class VPGResourceTestCase(base.TestCase):

    def test_create(self):
        domain = vnc_api.Domain(name='test-domain')
        fabric = vnc_api.Fabric(name='test-fabric', parent_obj=domain)
        node = vnc_api.Node(name='test-node', parent_obj=domain)

        vpg = create(
            node=node,
            fabric=fabric
        )
        self.assertEqual(vpg.name, make_name(node.name))
        self.assertEqual(vpg.parent_name, fabric.name)
        self.assertEqual(vpg.id_perms, vnc_api.IdPermsType(enable=True))

    def test_make_name(self):
        vpg_name = make_name('test-node.novalocal')
        standarized_name = 'dGVzdC1ub2RlLm5vdmFsb2NhbA=='

        self.assertEqual(vpg_name, 'vpg#{}'.format(standarized_name))

    def test_make_name_with_network(self):
        vpg_name = make_name('test-node.novalocal', 'tenant')
        name = 'dGVzdC1ub2RlLm5vdmFsb2NhbA=='
        network_name = 'dGVuYW50'
        expected_vpg_name = 'vpg#{name}#{network_name}'.format(
            name=name,
            network_name=network_name,
        )

        self.assertEqual(vpg_name, expected_vpg_name)

    def test_unzip_name(self):
        expected_node_name = 'my-n0de_'

        vmi_name = make_name(expected_node_name)
        node_name, _ = unzip_name(vmi_name)

        self.assertEqual(node_name, expected_node_name)

    def test_unzip_name_with_network(self):
        expected_node_name = 'my-n0de_'
        expected_network_name = 'my-net'

        vmi_name = make_name(expected_node_name, expected_network_name)
        node_name, network_name = unzip_name(vmi_name)

        self.assertEqual(node_name, expected_node_name)
        self.assertEqual(network_name, expected_network_name)
