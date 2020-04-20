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

from vnc_api import vnc_api

from networking_opencontrail.common import utils
from networking_opencontrail import resources
from networking_opencontrail.tests.base import IntegrationTestCase


@ddt.ddt
class TestVPGsAndVMIs(IntegrationTestCase):
    LAST_VLAN_ID = 100
    FABRIC = {'qfx-test-1': ['xe-0/0/0'],
              'qfx-test-2': ['xe-0/0/0',
                             'xe-1/1/1']}
    TOPOLOGY = {'compute-node': {'port-1':
                                 ('qfx-test-1', 'xe-0/0/0')},
                'compute-2': {'port-1':
                              ('qfx-test-2', 'xe-0/0/0'),
                              'port-2':
                              ('qfx-test-2', 'xe-1/1/1')}}

    @classmethod
    def setUpClass(cls):
        super(TestVPGsAndVMIs, cls).setUpClass()
        cls._vnc_api = vnc_api.VncApi(api_server_host=cls.contrail_ip)
        cls._cleanup_topology_queue = []
        cls._cleanup_fabric_queue = []

        try:
            cls._make_fake_fabric()
            cls._make_fake_topology()
        except Exception:
            cls.tearDownClass()
            raise

    @classmethod
    def tearDownClass(cls):
        super(TestVPGsAndVMIs, cls).tearDownClass()
        cls._cleanup()

    def setUp(self):
        super(TestVPGsAndVMIs, self).setUp()

        self.test_network, self.vlan_id = self._make_vlan_network()

    def tearDown(self):
        self._cleanup_vpgs()
        super(TestVPGsAndVMIs, self).tearDown()

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

    def _find_vmi(self, vmi_name):
        vmis = self.tf_list('virtual-machine-interface')
        return next((vmi['uuid'] for vmi in vmis
                     if vmi['fq_name'][-1] == vmi_name),
                    None)

    def _assert_vpg_deleted_or_not_ref(self, vpg_uuid, vmi_uuid):
        vpg = self.tf_get('virtual-port-group', vpg_uuid)
        if vpg:
            vpg = self.tf_get('virtual-port-group', vpg_uuid)
            self.assertFalse(self._check_vpg_contains_vmi_ref(
                vpg, vmi_uuid))

    def _assert_dm_vmi(self, vmi_uuid, net_uuid, vlan):
        """Assert that VMI with bindings for DM is created properly.

            1. VMI uuid exists
            2. VMI is connected only to given network
            3. VMI has right VLAN tag
            4. VMI has reference to one VPG and this VPG has reference to it
            5. VMI is tagged with label=__ML2__ tag
        """

        self.assertIsNotNone(vmi_uuid)
        vmi = self.tf_get('virtual-machine-interface', vmi_uuid)

        self.assertEqual(1, len(vmi.get_virtual_network_refs() or ()))
        self.assertEqual(net_uuid, vmi.get_virtual_network_refs()[0]['uuid'])

        vmi_properties = vmi.get_virtual_machine_interface_properties()
        self.assertIsNotNone(vmi_properties)
        self.assertEqual(vlan, vmi_properties.get_sub_interface_vlan_tag())

        self.assertEqual(1, len(vmi.get_virtual_port_group_back_refs() or ()))
        vpg_uuid = vmi.get_virtual_port_group_back_refs()[0]['uuid']
        vpg = self.tf_get('virtual-port-group', vpg_uuid)
        self.assertTrue(self._check_vpg_contains_vmi_ref(vpg, vmi_uuid))

        tag_names = [tag_ref["to"][-1] for tag_ref in vmi.get_tag_refs() or ()]
        self.assertIn("label=__ML2__", tag_names)

    def _check_vpg_contains_vmi_ref(self, vpg, vmi_uuid):
        vmi_refs = vpg.get_virtual_machine_interface_refs() or ()
        for ref in vmi_refs:
            if ref['uuid'] == vmi_uuid:
                return True
        return False

    def _make_vlan_network(self):
        vlan_id = self.LAST_VLAN_ID = self.LAST_VLAN_ID + 1
        net = {'name': 'test_vlan_{}_network'.format(vlan_id),
               'admin_state_up': True,
               'provider:network_type': 'vlan',
               'provider:physical_network': self.provider,
               'provider:segmentation_id': vlan_id,
               'tenant_id': self.project.id}
        network = self.q_create_network(**net)
        return network, vlan_id

    @classmethod
    def _make_fake_fabric(cls):
        try:
            fabric = cls._vnc_api.fabric_read(
                ["default-global-system-config", "fabric01"]
            )
            cls._fabric_uuid = fabric.get_uuid()
        except vnc_api.NoIdError:
            fabric = vnc_api.Fabric('fabric01')
            cls._fabric_uuid = cls._vnc_api.fabric_create(fabric)
        cls._cleanup_fabric_queue.append(('fabric', cls._fabric_uuid))

        for pr_name in cls.FABRIC:
            try:
                pr = cls._vnc_api.physical_router_read(
                    ["default-global-system-config", pr_name]
                )
                pr.set_fabric(fabric)
                pr_uuid = pr.get_uuid()
                cls._vnc_api.physical_router_update(pr)
            except vnc_api.NoIdError:
                pr = vnc_api.PhysicalRouter(pr_name)
                pr.set_fabric(fabric)
                pr_uuid = cls._vnc_api.physical_router_create(pr)
            cls._cleanup_fabric_queue.append(('physical_router', pr_uuid))

            for pi_name in cls.FABRIC[pr_name]:
                try:
                    pi = cls._vnc_api.physical_interface_read([
                        "default-global-system-config", pr_name, pi_name])
                    pi_uuid = pi.get_uuid()
                except vnc_api.NoIdError:
                    pi = vnc_api.PhysicalInterface(name=pi_name, parent_obj=pr)
                    pi_uuid = cls._vnc_api.physical_interface_create(pi)
                cls._cleanup_fabric_queue.append(
                    ('physical_interface', pi_uuid))

    @classmethod
    def _make_fake_topology(cls):
        for node_name in cls.TOPOLOGY:
            try:
                node = cls._vnc_api.node_read(
                    ["default-global-system-config", node_name]
                )
                node_uuid = node.get_uuid()
            except vnc_api.NoIdError:
                node = vnc_api.Node(node_name, node_hostname=node_name)
                node_uuid = cls._vnc_api.node_create(node)
            cls._cleanup_topology_queue.append(('node', node_uuid))

            for port_name, port_pi in cls.TOPOLOGY[node_name].items():
                try:
                    node_port = cls._vnc_api.port_read(
                        ["default-global-system-config", node_name, port_name]
                    )
                    port_uuid = node_port.get_uuid()
                except vnc_api.NoIdError:
                    ll_obj = vnc_api.LocalLinkConnection(
                        switch_info=port_pi[0],
                        port_id=port_pi[1])
                    bm_info = vnc_api.BaremetalPortInfo(
                        address='00-00-00-00-00-00',
                        local_link_connection=ll_obj)
                    node_port = vnc_api.Port(port_name, node,
                                             bms_port_info=bm_info)
                    port_uuid = cls._vnc_api.port_create(node_port)
                cls._cleanup_topology_queue.append(('port', port_uuid))

    def _cleanup_vpgs(self):
        fabric = self._vnc_api.fabric_read(id=self._fabric_uuid)
        for vpg_ref in fabric.get_virtual_port_groups() or ():
            vpg_uuid = vpg_ref['uuid']
            vpg = self._vnc_api.virtual_port_group_read(id=vpg_uuid)
            for vmi_ref in vpg.get_virtual_machine_interface_refs() or ():
                vmi = self._vnc_api.virtual_machine_interface_read(
                    vmi_ref["to"]
                )
                vpg.del_virtual_machine_interface(vmi)
            self._vnc_api.virtual_port_group_update(vpg)
            self._vnc_api.virtual_port_group_delete(id=vpg.uuid)

    @classmethod
    def _cleanup(cls):
        reraise = False

        for queue in [cls._cleanup_fabric_queue, cls._cleanup_topology_queue]:
            for resource, res_uuid in reversed(queue):
                try:
                    del_func = getattr(cls._vnc_api,
                                       "{}_delete".format(resource))
                    del_func(id=res_uuid)
                except vnc_api.NoIdError:
                    pass
                except Exception:
                    reraise = True

        if reraise:
            raise
