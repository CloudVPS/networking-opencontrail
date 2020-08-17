# Copyright (c) 2019 OpenStack Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


import ddt

from networking_opencontrail import resources
from networking_opencontrail.resources import utils
from networking_opencontrail.tests.base import FabricTestCase


@ddt.ddt
class TestVPGsAndVMIs(FabricTestCase):
    def test_create_vlan_port_on_node(self):
        port = {'name': 'test_fabric_port',
                'network_id': self.test_network['network']['id'],
                'binding:host_id': 'compute-node',
                'device_owner': 'compute:fake-nova',
                'tenant_id': self.project.id}
        self.q_create_port(**port)

        vmi_name = resources.vmi.make_name(
            self.test_network['network']['id'],
            'compute-node'
        )
        vmi_uuid = utils.make_uuid(vmi_name)
        self._assert_dm_vmi(vmi_uuid,
                            self.test_network['network']['id'],
                            self.vlan_id)

    def test_create_two_ports_on_two_nodes(self):
        port = {'name': 'test_fabric_port',
                'network_id': self.test_network['network']['id'],
                'binding:host_id': 'compute-node',
                'device_owner': 'compute:fake-nova',
                'tenant_id': self.project.id}
        self.q_create_port(**port)

        port.update({'device_id': 'vm-2',
                     'binding:host_id': 'compute-2'})
        self.q_create_port(**port)

        vpg_uuids = set()
        expected_bindings = [('compute-node', [('qfx-test-1', 'xe-0/0/0')]),
                             ('compute-2', [('qfx-test-2', 'xe-0/0/0'),
                                            ('qfx-test-2', 'xe-1/1/1')])]
        for node_name, physical_interfaces in expected_bindings:
            vmi_name = resources.vmi.make_name(
                self.test_network['network']['id'],
                node_name
            )
            vmi_uuid = utils.make_uuid(vmi_name)
            self._assert_dm_vmi(vmi_uuid,
                                self.test_network['network']['id'],
                                self.vlan_id)

            vmi = self.tf_get('virtual-machine-interface', vmi_uuid)
            vpg_uuids.add(vmi.get_virtual_port_group_back_refs()[0]['uuid'])

        self.assertEqual(2, len(vpg_uuids))

    def test_create_unmanaged_port(self):
        port = {'name': 'test_fabric_port',
                'network_id': self.test_network['network']['id'],
                'binding:host_id': 'compute-node',
                'device_owner': 'not-compute:fake',
                'tenant_id': self.project.id}
        self.q_create_port(**port)

        vmi_name = resources.vmi.make_name(
            self.test_network['network']['id'],
            'compute-node'
        )
        vmi_uuid = self._find_vmi(vmi_name)
        self.assertIsNone(vmi_uuid)

    def test_create_port_in_non_vlan_network(self):
        net = {'name': 'test_notvlan_network',
               'admin_state_up': True,
               'provider:network_type': 'local',
               'tenant_id': self.project.id}
        network = self.q_create_network(**net)

        port = {'name': 'test_fabric_port',
                'network_id': network['network']['id'],
                'binding:host_id': 'compute-node',
                'device_owner': 'compute:fake-nova',
                'tenant_id': self.project.id}
        self.q_create_port(**port)

        vmi_name = resources.vmi.make_name(
            self.test_network['network']['id'],
            'compute-node'
        )
        vmi_uuid = self._find_vmi(vmi_name)
        self.assertIsNone(vmi_uuid)

    def test_update_to_managed(self):
        port = {'name': 'test_fabric_port',
                'network_id': self.test_network['network']['id'],
                'binding:host_id': 'compute-node',
                'device_owner': 'compute:fake-nova',
                'tenant_id': self.project.id}
        q_port = self.q_create_port(**port)

        vmi_name = resources.vmi.make_name(
            self.test_network['network']['id'],
            'compute-node'
        )
        vmi_uuid = self._find_vmi(vmi_name)
        self._assert_dm_vmi(vmi_uuid,
                            self.test_network['network']['id'],
                            self.vlan_id)

        self.q_update_port(q_port, **{'binding:host_id': 'compute-2'})

        self.assertIsNone(self._find_vmi(vmi_name))
        vmi_name_2 = resources.vmi.make_name(
            self.test_network['network']['id'],
            'compute-2'
        )
        vmi_uuid_2 = self._find_vmi(vmi_name_2)
        self._assert_dm_vmi(vmi_uuid_2,
                            self.test_network['network']['id'],
                            self.vlan_id)

    def test_update_to_unmanaged(self):
        port = {'name': 'test_fabric_port',
                'network_id': self.test_network['network']['id'],
                'binding:host_id': 'compute-node',
                'device_owner': 'compute:fake-nova',
                'tenant_id': self.project.id}
        q_port = self.q_create_port(**port)

        vmi_name = resources.vmi.make_name(
            self.test_network['network']['id'],
            'compute-node'
        )
        vmi_uuid = self._find_vmi(vmi_name)
        self._assert_dm_vmi(vmi_uuid,
                            self.test_network['network']['id'],
                            self.vlan_id)

        vmi = self.tf_get('virtual-machine-interface', vmi_uuid)
        vpg_uuid = vmi.get_virtual_port_group_back_refs()[0]['uuid']

        change = {'device_owner': 'not-compute:fake'}
        self.q_update_port(q_port, **change)

        vmi_uuid = self._find_vmi(vmi_name)
        self.assertIsNone(vmi_uuid)
        self._assert_vpg_deleted_or_not_ref(vpg_uuid, vmi_uuid)

    def test_delete_last_port(self):
        q_port = {'name': 'test_fabric_port',
                  'network_id': self.test_network['network']['id'],
                  'binding:host_id': 'compute-node',
                  'device_id': 'vm-1',
                  'device_owner': 'compute:fake-nova',
                  'tenant_id': self.project.id}
        q_port = self.q_create_port(**q_port)

        vmi_name = resources.vmi.make_name(
            self.test_network['network']['id'],
            'compute-node'
        )
        vmi_uuid = self._find_vmi(vmi_name)
        self.assertIsNotNone(vmi_uuid)

        vmi = self.tf_get('virtual-machine-interface', vmi_uuid)
        vpg_uuid = vmi.get_virtual_port_group_back_refs()[0]['uuid']

        self.q_delete_port(q_port)

        self.assertIsNone(self._find_vmi(vmi_name))
        self._assert_vpg_deleted_or_not_ref(vpg_uuid, vmi_uuid)

    def test_delete_port_when_other_exists_not_removes_dm_bindings(self):
        port = {'name': 'test_fabric_port',
                'network_id': self.test_network['network']['id'],
                'binding:host_id': 'compute-node',
                'device_id': 'vm-1',
                'device_owner': 'compute:fake-nova',
                'tenant_id': self.project.id}
        q_port = self.q_create_port(**port)

        port.update({'device_id': 'vm-2'})
        self.q_create_port(**port)

        vmi_name = resources.vmi.make_name(
            self.test_network['network']['id'],
            'compute-node'
        )
        self.assertIsNotNone(self._find_vmi(vmi_name))

        self.q_delete_port(q_port)

        self.assertIsNotNone(self._find_vmi(vmi_name))

    def test_three_ports_on_node(self):
        """Create three ports in two networks for the same Node, remove two

        There should be only one VMI per network on node. After remove port,
        VPG should not have reference to it any more.
        """

        port = {'name': 'test_fabric_port',
                'network_id': self.test_network['network']['id'],
                'binding:host_id': 'compute-node',
                'device_id': 'vm-1',
                'device_owner': 'compute:fake-nova',
                'tenant_id': self.project.id}
        self.q_create_port(**port)

        port.update({'device_id': 'vm-2'})
        q_port_2 = self.q_create_port(**port)

        network_2, vlan_2 = self._make_vlan_network()
        port.update({'device_id': 'vm-3',
                     'network_id': network_2['network']['id']})
        q_port_3 = self.q_create_port(**port)

        vmi_uuids = []
        vpg_uuids = set()
        expected_bindings = [(self.test_network, self.vlan_id, 'compute-node'),
                             (network_2, vlan_2, 'compute-node')]
        for network, vlan_id, node_name in expected_bindings:
            vmi_name = resources.vmi.make_name(
                network['network']['id'],
                node_name
            )
            vmi_uuid = self._find_vmi(vmi_name)
            self._assert_dm_vmi(vmi_uuid,
                                network['network']['id'],
                                vlan_id)
            vmi_uuids.append(vmi_uuid)

            vmi = self.tf_get('virtual-machine-interface', vmi_uuid)
            vpg_uuids.add(vmi.get_virtual_port_group_back_refs()[0]['uuid'])

        self.assertEqual(1, len(vpg_uuids))

        self.q_delete_port(q_port_2)
        self.q_delete_port(q_port_3)

        vpg = self.tf_get('virtual-port-group', vpg_uuids.pop())
        self.assertTrue(self._check_vpg_contains_vmi_ref(vpg, vmi_uuids[0]))
        self.assertFalse(self._check_vpg_contains_vmi_ref(vpg, vmi_uuids[1]))

        vmi = self.tf_get('virtual-machine-interface', vmi_uuids[1])
        self.assertIsNone(vmi)
