# -*- coding: utf-8 -*-
# Copyright (c) 2018 OpenStack Foundation
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

from networking_opencontrail.repository import ml2_tag_manager
from networking_opencontrail.tests.base import IntegrationTestCase


class TestManageNetwork(IntegrationTestCase):

    def test_create_network_vlan(self):
        network_schema = {
            'name': 'test_vlan_network',
            'provider:network_type': 'vlan',
            'provider:physical_network': 'public',
        }
        wrapped_q_network = self.q_create_network(**network_schema)
        q_network = wrapped_q_network['network']

        network = self.tf_get('virtual-network', q_network['id'])

        self.assertEqual(network.name, q_network['name'])
        self.assertEqual(network.get_uuid(), q_network['id'])

    def test_update_network_vlan(self):
        network_schema = {
            'name': 'old_name',
            'provider:network_type': 'vlan',
            'provider:physical_network': 'public',

        }
        wrapped_q_network = self.q_create_network(**network_schema)

        new_name = 'new_name'
        wrapped_q_network = self.q_update_network(wrapped_q_network,
                                                  name=new_name)

        network = self.tf_get('virtual-network',
                              wrapped_q_network['network']['id'])
        self.assertEqual(network.get_display_name(), new_name)
        self.assertEqual(network.name, network_schema['name'])

    def test_delete_network_vlan(self):
        network_schema = {
            'name': 'test_vlan_network',
            'provider:network_type': 'vlan',
            'provider:physical_network': 'public',
        }
        wrapped_q_network = self.q_create_network(**network_schema)
        q_network = wrapped_q_network['network']
        self.q_delete_network(wrapped_q_network)

        tf_network = self.tf_get('virtual-network', q_network['id'])
        self.assertIsNone(tf_network)

    def test_created_network_is_tagged(self):
        network_schema = {
            'name': 'test_vlan_network',
            'provider:network_type': 'vlan',
            'provider:physical_network': 'public',
        }
        wrapped_q_network = self.q_create_network(**network_schema)
        q_network = wrapped_q_network['network']

        network = self.tf_get('virtual-network', q_network['id'])
        network_tag_fq_name = network.get_tag_refs()[0]['to']
        self.assertEqual(network_tag_fq_name, ml2_tag_manager.FQ_NAME)

    def test_updated_network_is_tagged(self):
        network_schema = {
            'name': 'old_name',
            'provider:network_type': 'vlan',
            'provider:physical_network': 'public',

        }
        wrapped_q_network = self.q_create_network(**network_schema)

        new_name = 'new_name'
        wrapped_q_network = self.q_update_network(wrapped_q_network,
                                                  name=new_name)

        network = self.tf_get('virtual-network',
                              wrapped_q_network['network']['id'])
        network_tag_fq_name = network.get_tag_refs()[0]['to']
        self.assertEqual(network_tag_fq_name, ml2_tag_manager.FQ_NAME)
