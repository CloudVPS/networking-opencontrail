# Copyright (c) 2020 OpenStack Foundation
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
import uuid

from networking_opencontrail.repository.utils import tagger
from networking_opencontrail.tests.base import FabricTestCase


class TestLogicalRouterBase(FabricTestCase):
    """Base class for Logical Router testing"""
    DRIVER_NAME = \
        'networking_opencontrail.l3.service_provider.TFL3ServiceProvider'
    FLAVOR_BODY = {
        'flavor': {
            'service_type': 'L3_ROUTER_NAT',
        }
    }
    PROFILE_BODY = {
        'service_profile': {
            'driver': DRIVER_NAME
        }
    }

    def setUp(self):
        super(TestLogicalRouterBase, self).setUp()

        self.test_flavor = self.create_test_l3_flavor()

    def tearDown(self):
        super(TestLogicalRouterBase, self).tearDown()

        self.delete_test_l3_flavor(self.test_flavor)

    def create_test_l3_flavor(self):
        """Creates a network flavor used for tests.

        This method creates a flavor and a service profile and associates them.
        :return: network flavor
        :rtype: dict
        """

        flavor = self.neutron.create_flavor(self.FLAVOR_BODY)['flavor']
        profile = self.neutron.create_service_profile(self.PROFILE_BODY)

        profile_to_associate = {
            'service_profile': {
                'id': profile['service_profile']['id']
            }
        }
        self.neutron.associate_flavor(flavor['id'], profile_to_associate)

        return self.neutron.list_flavors(id=flavor['id'])['flavors'][0]

    def delete_test_l3_flavor(self, flavor):
        """Deletes network flavor created for tests."""
        service_profile_ids = flavor.get('service_profile_ids', ())
        for profile_id in service_profile_ids:
            self.neutron.disassociate_flavor(flavor['id'], profile_id)
            self.neutron.delete_service_profile(profile_id)
        self.neutron.delete_flavor(flavor['id'])

    def assert_tf_router(self, router_id, expected):
        tf_router = self.tf_get('logical-router', router_id)
        tf_dict = {
            'name': tf_router.name,
            'uuid': tf_router.get_uuid(),
            'project_id': tf_router.parent_uuid,
            'lr_type': tf_router.get_logical_router_type(),
        }
        expected_physical_routers = expected.pop('physical_routers')
        self.assertDictEqual(tf_dict, expected)
        self.assertTrue(tagger.belongs_to_ntf(tf_router))
        actual_physical_routers = sorted(
            pr_ref['to'][-1]
            for pr_ref in tf_router.get_physical_router_refs()
        )
        self.assertTrue(all(
            pr in actual_physical_routers for pr in expected_physical_routers
        ))

    def add_router_interface(self, router, subnet):
        subnet_info = {'subnet_id': subnet['id']}
        return self.neutron.add_interface_router(router['id'], subnet_info)

    def remove_router_interface(self, router, subnet):
        subnet_info = {'subnet_id': subnet['id']}
        return self.neutron.remove_interface_router(router['id'], subnet_info)


class TestLogicalRouterCRB(TestLogicalRouterBase):
    """Integration tests for Logical Router management.

    Following scenarios are tested:
    1. Test if Logical Router is created properly:
        - Create a test LR in Neutron.
        - Check if LR was created in TF.
        - Verify that LR in TF has all fields set properly.
        Especially check all spines were assigned to LR.
    """
    FABRIC = {
        'qfx-leaf-1': ['xe-0/0/0', 'xe-0/0/1'],
        'qfx-leaf-2': ['xe-0/0/0', 'xe-0/0/1'],
        'qfx-spine-1': ['xe-0/0/0', 'xe-0/0/1'],
        'qfx-spine-2': ['xe-0/0/0', 'xe-0/0/1']
    }
    PR_ROLES = {
        'qfx-leaf-1': {
            'physical-role': 'leaf',
            'overlay-role': 'crb-access'
        },
        'qfx-leaf-2': {
            'physical-role': 'leaf',
            'overlay-role': 'crb-access'
        },
        'qfx-spine-1': {
            'physical-role': 'spine',
            'overlay-role': 'crb-gateway'
        },
        'qfx-spine-2': {
            'physical-role': 'spine',
            'overlay-role': 'crb-gateway'
        }
    }
    TOPOLOGY = {}

    def test_create(self):
        router = {
            'name': 'test-router',
            'admin_state_up': True,
            'flavor_id': self.test_flavor['id'],
        }

        q_router = self.q_create_logical_router(router)['router']

        expected = {
            'name': q_router.get('name'),
            'uuid': q_router.get('id'),
            'project_id': str(uuid.UUID(q_router.get('project_id'))),
            'lr_type': 'vxlan-routing',
            'physical_routers': ['qfx-spine-1', 'qfx-spine-2'],
        }
        self.assert_tf_router(router_id=q_router['id'], expected=expected)


class TestLogicalRouterERB(TestLogicalRouterBase):
    """Integration tests for Logical Router management.

    Following scenarios are tested:
    1. Test if Logical Router is created properly:
        - Create a test LR in Neutron.
        - Check if LR was created in TF.
        - Verify that LR in TF has all fields set properly.
        Especially check all leaves were assigned to LR.
    """
    FABRIC = {
        'qfx-leaf-1': ['xe-0/0/0', 'xe-0/0/1'],
        'qfx-leaf-2': ['xe-0/0/0', 'xe-0/0/1'],
        'qfx-spine': ['xe-0/0/0', 'xe-0/0/1'],
    }
    PR_ROLES = {
        'qfx-leaf-1': {
            'physical-role': 'leaf',
            'overlay-role': 'erb-ucast-gateway'
        },
        'qfx-leaf-2': {
            'physical-role': 'leaf',
            'overlay-role': 'erb-ucast-gateway'
        },
        'qfx-spine': {
            'physical-role': 'spine',
            'overlay-role': 'route-reflector'
        }
    }
    TOPOLOGY = {}

    def test_create(self):
        router = {
            'name': 'test-router',
            'admin_state_up': True,
            'flavor_id': self.test_flavor['id'],
        }

        q_router = self.q_create_logical_router(router)['router']

        expected = {
            'name': q_router.get('name'),
            'uuid': q_router.get('id'),
            'project_id': str(uuid.UUID(q_router.get('project_id'))),
            'lr_type': 'vxlan-routing',
            'physical_routers': sorted(['qfx-leaf-1', 'qfx-leaf-2']),
        }
        self.assert_tf_router(router_id=q_router['id'], expected=expected)


class TestLogicalRouterCommon(TestLogicalRouterBase):
    """Integration tests for Logical Router management.

        Following scenarios are tested:
        1. Test if Logical Router is deleted:
            - Create a test LR in Neutron.
            - Delete the LR from Neutron.
            - Verify that LR is deleted in TF.

        2. Test if routers not handled by NTF L3 flavor are ignored:
            - Create a test LR in Neutron.
            - Verify that LR was not created in TF.
    """
    def test_delete(self):
        router = {
            'name': 'test-router',
            'admin_state_up': True,
            'flavor_id': self.test_flavor['id'],
        }

        q_router = self.q_create_logical_router(router)['router']
        tf_router = self.tf_get('logical-router', q_router['id'])

        self.assertIsNotNone(tf_router)

        self.q_delete_resource(q_router)
        tf_router = self.tf_get('logical-router', q_router['id'])

        self.assertIsNone(tf_router)

    def test_ignore(self):
        router = {
            'name': 'test-router',
            'admin_state_up': True,
        }

        q_router = self.q_create_logical_router(router)['router']
        tf_router = self.tf_get('logical-router', q_router['id'])

        self.assertIsNone(tf_router)


class TestLogicalRouterInterfaces(TestLogicalRouterBase):
    """Integration tests for router interfaces management.

    Following scenario is tested:
    1. Test adding and removing interfaces to Logical Router:
        - Create a test router in Neutron.
        - Create two test networks and two test subnets in Neutron.
        - Add one router interface connected to subnet 1.
        - Add second router interface connected to subnet 2.
        - Verify that VMIs connecting the LR to the proper VNs
            are created in TF.
        - Remove the interfaces from the router in Neutron.
        - Verify that VMIs were deleted from TF.
    """

    def test_add_and_remove_interface(self):
        router = {
            'name': 'test-router',
            'admin_state_up': True,
            'flavor_id': self.test_flavor['id'],
        }
        q_router = self.q_create_logical_router(router)['router']

        network_1 = {
            'name': 'test-lr-network-1',
            'admin_state_up': True,
            'provider:network_type': 'local',
        }
        q_network_1 = self.q_create_network(**network_1)['network']

        subnet_1 = {
            'name': 'test-subnet-1',
            'cidr': '10.10.11.0/24',
            'network_id': q_network_1['id'],
            'gateway_ip': '10.10.11.1',
            'ip_version': 4,
        }
        q_subnet_1 = self.q_create_subnet(**subnet_1)['subnet']

        network_2 = {
            'name': 'test-lr-network-2',
            'admin_state_up': True,
            'provider:network_type': 'local',
        }
        q_network_2 = self.q_create_network(**network_2)['network']

        subnet_2 = {
            'name': 'test-subnet-2',
            'cidr': '20.20.22.0/24',
            'network_id': q_network_2['id'],
            'gateway_ip': '20.20.22.1',
            'ip_version': 4,
        }
        q_subnet_2 = self.q_create_subnet(**subnet_2)['subnet']

        response_1 = self.add_router_interface(q_router, q_subnet_1)
        response_2 = self.add_router_interface(q_router, q_subnet_2)

        vmi_1 = self.tf_get('virtual-machine-interface', response_1['port_id'])
        vmi_2 = self.tf_get('virtual-machine-interface', response_2['port_id'])

        self.assertIsNotNone(vmi_1)
        self.assertIsNotNone(vmi_2)

        self._assert_lr_vmi(vmi_1, q_router['id'], q_network_1['id'])
        self._assert_lr_vmi(vmi_2, q_router['id'], q_network_2['id'])

        self.remove_router_interface(q_router, q_subnet_1)
        self.remove_router_interface(q_router, q_subnet_2)

        vmi_1 = self.tf_get('virtual-machine-interface', response_1['port_id'])
        vmi_2 = self.tf_get('virtual-machine-interface', response_2['port_id'])
        self.assertIsNone(vmi_1)
        self.assertIsNone(vmi_2)

    def _assert_lr_vmi(self, vmi, router_id, network_id):
        lr_back_refs = vmi.get_logical_router_back_refs() or ()
        self.assertEqual(len(lr_back_refs), 1)
        self.assertEqual(lr_back_refs[0]['uuid'], router_id)

        vn_refs = vmi.get_virtual_network_refs() or ()
        self.assertEqual(len(vn_refs), 1)
        self.assertEqual(vn_refs[0]['uuid'], network_id)
