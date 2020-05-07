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

from networking_opencontrail.tests.base import IntegrationTestCase

from networking_opencontrail.repository.utils.tag import ml2_tag_manager


class TestLogicalRouters(IntegrationTestCase):
    """Integration tests for Logical Router management.

    Following scenarios are tested:
    1. Test if Logical Router is created properly:
        - Create a test LR in Neutron.
        - Check if LR was created in TF.
        - Verify that LR in TF has all fields set properly.

    2. Test if Logical Router is deleted:
        - Create a test LR in Neutron.
        - Delete the LR from Neutron.
        - Verify that LR is deleted in TF.

    3. Test if routers not handled by NTF L3 flavor are ignored:
        - Create a test LR in Neutron.
        - Verify that LR was not created in TF.
    """

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
        super(TestLogicalRouters, self).setUp()

        self.test_flavor = self.create_test_l3_flavor()

    def tearDown(self):
        super(TestLogicalRouters, self).tearDown()

        self.delete_test_l3_flavor(self.test_flavor)

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
            'tag_fq_name': ml2_tag_manager.FQ_NAME,
        }

        tf_router = self.tf_get('logical-router', q_router['id'])
        tf_dict = {
            'name': tf_router.name,
            'uuid': tf_router.get_uuid(),
            'project_id': tf_router.parent_uuid,
            'lr_type': tf_router.get_logical_router_type(),
            'tag_fq_name': tf_router.get_tag_refs()[0]['to'],
        }

        self.assertDictEqual(tf_dict, expected)

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
