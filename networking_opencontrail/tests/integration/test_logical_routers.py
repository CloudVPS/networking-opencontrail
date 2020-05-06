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

from networking_opencontrail.repository.utils.tag import ml2_tag_manager
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
            'tag_fq_name': tf_router.get_tag_refs()[0]['to'],
        }
        expected_physical_routers = expected.pop('physical_routers')
        self.assertDictEqual(tf_dict, expected)
        actual_physical_routers = sorted(
            pr_ref['to'][-1]
            for pr_ref in tf_router.get_physical_router_refs()
        )
        self.assertTrue(all(
            pr in actual_physical_routers for pr in expected_physical_routers
        ))


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
            'tag_fq_name': ml2_tag_manager.FQ_NAME,
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
            'tag_fq_name': ml2_tag_manager.FQ_NAME,
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
