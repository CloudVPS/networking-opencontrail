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
        pr = vnc_api.PhysicalRouter(name='test-pr', parent_obj=domain)
        physical_interfaces = [
            vnc_api.PhysicalInterface(name='test-pi-1', parent_obj=pr),
            vnc_api.PhysicalInterface(name='test-pi-2', parent_obj=pr),
            vnc_api.PhysicalInterface(name='test-pi-3', parent_obj=pr),
        ]

        vpg = create(
            node=node,
            physical_interfaces=physical_interfaces,
            fabric=fabric
        )
        self.assertEqual(vpg.name, make_name(node.name))
        self.assertEqual(vpg.parent_name, fabric.name)
        self.assertEqual(vpg.id_perms, vnc_api.IdPermsType(enable=True))

        expected_physical_interface_refs = []
        for physical_interface in physical_interfaces:
            expected_physical_interface_refs.append(
                {'to': physical_interface.fq_name, 'attr': None}
            )

        self.assertEqual(
            vpg.physical_interface_refs, expected_physical_interface_refs)

    def test_make_name(self):
        node = vnc_api.Node(name='test-node.novalocal')
        vpg_name = make_name(node.name)

        self.assertEqual(vpg_name, 'vpg#test-node.novalocal')

    def test_unzip_name(self):
        expected_node_name = 'my-n0de_'

        vmi_name = make_name(expected_node_name)
        node_name = unzip_name(vmi_name)

        self.assertEqual(node_name, expected_node_name)
