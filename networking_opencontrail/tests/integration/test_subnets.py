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
import uuid

from networking_opencontrail.resources.subnet import get_dhcp_option_list
from networking_opencontrail.resources.subnet import get_host_routes
from networking_opencontrail.tests.base import IntegrationTestCase


class TestSubnets(IntegrationTestCase):

    def setUp(self):
        super(TestSubnets, self).setUp()
        net = {
            'name': 'test_subnet_network',
            'admin_state_up': True,
            'provider:network_type': 'local',
        }
        self.test_network = self.q_create_network(**net)

    def test_create_subnet(self):
        """Create subnet with properties."""
        subnet = {
            'name': 'test_subnet',
            'cidr': '10.10.11.0/24',
            'network_id': self.test_network['network']['id'],
            'gateway_ip': '10.10.11.1',
            'ip_version': 4,
            'allocation_pools': [
                {
                    'start': '10.10.11.33',
                    'end': '10.10.11.55'
                }
            ],
            'dns_nameservers': ['10.10.11.22', '10.10.11.23'],
            'host_routes': [
                {
                    'nexthop': '10.10.11.1',
                    'destination': '1.1.1.0/24'
                }
            ]
        }
        q_subnet = self.q_create_subnet(**subnet)
        alloc_pool_start = q_subnet['subnet']['allocation_pools'][0]['start']
        alloc_pools_end = q_subnet['subnet']['allocation_pools'][0]['end']
        dns_nameservers = q_subnet['subnet']['dns_nameservers']
        expected = {
            'name': q_subnet['subnet']['name'],
            'network_id': q_subnet['subnet']['network_id'],
            'cidr': q_subnet['subnet']['cidr'],
            'gateway_ip': q_subnet['subnet']['gateway_ip'],
            'id': q_subnet['subnet']['id'],
            'allocation_pools_start': alloc_pool_start,
            'allocation_pools_end': alloc_pools_end,
            'dhcp_option_list': get_dhcp_option_list(dns_nameservers),
            'host_routes': get_host_routes(q_subnet['subnet']['host_routes'])
        }

        sub = self._get_subnet_from_network(q_subnet['subnet']['id'],
                                            self.test_network['network']['id'])

        tf_network = self.tf_get('virtual-network',
                                 self.test_network['network']['id'])

        self.assertIsNotNone(sub)

        sub_ip = sub.get_subnet()
        contrail_dict = {
            'name': sub.get_subnet_name(),
            'network_id': tf_network.get_uuid(),
            'cidr': '/'.join([sub_ip.get_ip_prefix() or '',
                              str(sub_ip.get_ip_prefix_len() or '')]),
            'gateway_ip': sub.get_default_gateway(),
            'id': sub.get_subnet_uuid(),
            'allocation_pools_start': sub.get_allocation_pools()[0].start,
            'allocation_pools_end': sub.get_allocation_pools()[0].end,
            'dhcp_option_list': sub.get_dhcp_option_list(),
            'host_routes': sub.get_host_routes()
        }

        self.assertDictEqual(expected, contrail_dict)

    def test_add_second_subnet(self):
        """Create second subnet with properties."""
        subnet_1 = {
            'name': 'test_subnet_1',
            'cidr': '10.10.11.0/24',
            'network_id': self.test_network['network']['id'],
            'gateway_ip': '10.10.11.1',
            'ip_version': 4,
            'allocation_pools': [
                {
                    'start': '10.10.11.33',
                    'end': '10.10.11.55'
                }
            ],
            'dns_nameservers': ['10.10.11.22', '10.10.11.23'],
            'host_routes': [
                {
                    'nexthop': '10.10.11.1',
                    'destination': '1.1.1.0/24'
                }
            ]
        }
        q_subnet_1 = self.q_create_subnet(**subnet_1)

        subnet_2 = {
            'name': 'test_subnet_1',
            'cidr': '20.20.22.0/24',
            'network_id': self.test_network['network']['id'],
            'gateway_ip': '20.20.22.1',
            'ip_version': 4,
            'allocation_pools': [
                {
                    'start': '20.20.22.88',
                    'end': '20.20.22.108'
                }
            ],
            'dns_nameservers': ['20.20.22.15', '20.20.22.19'],
            'host_routes': [
                {
                    'nexthop': '20.20.22.1',
                    'destination': '1.2.3.0/24'
                }
            ]
        }
        q_subnet_2 = self.q_create_subnet(**subnet_2)
        alloc_pool_start = q_subnet_1['subnet']['allocation_pools'][0]['start']
        alloc_pool_end = q_subnet_1['subnet']['allocation_pools'][0]['end']
        dns_nameservers = q_subnet_1['subnet']['dns_nameservers']
        expected_1 = {
            'name': q_subnet_1['subnet']['name'],
            'network_id': q_subnet_1['subnet']['network_id'],
            'cidr': q_subnet_1['subnet']['cidr'],
            'gateway_ip': q_subnet_1['subnet']['gateway_ip'],
            'id': q_subnet_1['subnet']['id'],
            'allocation_pools_start': alloc_pool_start,
            'allocation_pools_end': alloc_pool_end,
            'dhcp_option_list': get_dhcp_option_list(dns_nameservers),
            'host_routes': get_host_routes(q_subnet_1['subnet']['host_routes'])
        }
        alloc_pool_start = q_subnet_2['subnet']['allocation_pools'][0]['start']
        alloc_pools_end = q_subnet_2['subnet']['allocation_pools'][0]['end']
        dns_nameservers = q_subnet_2['subnet']['dns_nameservers']
        expected_2 = {
            'name': q_subnet_2['subnet']['name'],
            'network_id': q_subnet_2['subnet']['network_id'],
            'cidr': q_subnet_2['subnet']['cidr'],
            'gateway_ip': q_subnet_2['subnet']['gateway_ip'],
            'id': q_subnet_2['subnet']['id'],
            'allocation_pools_start': alloc_pool_start,
            'allocation_pools_end': alloc_pools_end,
            'dhcp_option_list': get_dhcp_option_list(dns_nameservers),
            'host_routes': get_host_routes(q_subnet_2['subnet']['host_routes'])
        }
        sub_1 = self._get_subnet_from_network(
            q_subnet_1['subnet']['id'],
            self.test_network['network']['id']
        )

        sub_2 = self._get_subnet_from_network(
            q_subnet_2['subnet']['id'],
            self.test_network['network']['id']
        )

        tf_network = self.tf_get('virtual-network',
                                 self.test_network['network']['id'])

        self.assertIsNotNone(sub_1)
        self.assertIsNotNone(sub_2)

        for sub, expected in zip((sub_1, sub_2), (expected_1, expected_2)):
            sub_ip = sub.get_subnet()
            contrail_dict = {
                'name': sub.get_subnet_name(),
                'network_id': tf_network.get_uuid(),
                'cidr': '/'.join([sub_ip.get_ip_prefix() or '',
                                  str(sub_ip.get_ip_prefix_len() or '')]),
                'gateway_ip': sub.get_default_gateway(),
                'id': sub.get_subnet_uuid(),
                'allocation_pools_start': sub.get_allocation_pools()[0].start,
                'allocation_pools_end': sub.get_allocation_pools()[0].end,
                'dhcp_option_list': sub.get_dhcp_option_list(),
                'host_routes': sub.get_host_routes()
            }

            self.assertDictEqual(expected, contrail_dict)

    def test_update_subnet(self):
        """Update subnet properties.

        Update of gateway is called which causes the exception.
        It happens even if gateway isn't changed explicitly.

        Exception message:
        "Update Subnet Failed: BadRequest: Bad subnet request: update of
        gateway is not supported."
        """
        subnet = {
            'name': 'test_subnet',
            'cidr': '10.10.11.0/24',
            'network_id': self.test_network['network']['id'],
            'gateway_ip': '10.10.11.1',
            'ip_version': 4,
            'allocation_pools': [
                {
                    'start': '10.10.11.33',
                    'end': '10.10.11.55'
                }
            ],
            'dns_nameservers': ['10.10.11.22', '10.10.11.23'],
            'host_routes': [
                {
                    'nexthop': '10.10.11.1',
                    'destination': '1.1.1.0/24'
                }
            ]
        }
        q_subnet = self.q_create_subnet(**subnet)

        sub = self._get_subnet_from_network(q_subnet['subnet']['id'],
                                            self.test_network['network']['id'])
        self.assertIsNotNone(sub)

        changed_fields = {
            'name': 'new_subnet_name',
            'gateway_ip': '10.10.11.2',
            'allocation_pools': [
                {
                    'start': '10.10.11.36',
                    'end': '10.10.11.55'
                }
            ],
            'dns_nameservers': ['10.10.11.22', '10.10.11.25'],
            'host_routes': [
                {
                    'nexthop': '10.10.11.1',
                    'destination': '1.1.2.0/24'
                }
            ]
        }
        q_subnet = self.q_update_subnet(q_subnet, **changed_fields)
        alloc_pool_start = q_subnet['subnet']['allocation_pools'][0]['start']
        alloc_pools_end = q_subnet['subnet']['allocation_pools'][0]['end']
        dns_nameservers = q_subnet['subnet']['dns_nameservers']
        expected = {
            'name': q_subnet['subnet']['name'],
            'network_id': q_subnet['subnet']['network_id'],
            'cidr': q_subnet['subnet']['cidr'],
            'gateway_ip': q_subnet['subnet']['gateway_ip'],
            'id': q_subnet['subnet']['id'],
            'allocation_pools_start': alloc_pool_start,
            'allocation_pools_end': alloc_pools_end,
            'dhcp_option_list': get_dhcp_option_list(dns_nameservers),
            'host_routes': get_host_routes(q_subnet['subnet']['host_routes'])
        }

        sub = self._get_subnet_from_network(q_subnet['subnet']['id'],
                                            self.test_network['network']['id'])

        tf_network = self.tf_get('virtual-network',
                                 self.test_network['network']['id'])

        sub_ip = sub.get_subnet()
        s = {
            'name': sub.get_subnet_name(),
            'network_id': tf_network.get_uuid(),
            'cidr': '/'.join([sub_ip.get_ip_prefix() or '',
                              str(sub_ip.get_ip_prefix_len() or '')]),
            'gateway_ip': sub.get_default_gateway(),
            'id': sub.get_subnet_uuid(),
            'allocation_pools_start': sub.get_allocation_pools()[0].start,
            'allocation_pools_end': sub.get_allocation_pools()[0].end,
            'dhcp_option_list': sub.get_dhcp_option_list(),
            'host_routes': sub.get_host_routes()
        }

        self.assertDictEqual(expected, s)

    def test_delete_subnet(self):
        """Delete subnet with properties."""
        subnet = {
            'name': 'test_subnet',
            'cidr': '10.10.11.0/24',
            'network_id': self.test_network['network']['id'],
            'gateway_ip': '10.10.11.1',
            'ip_version': 4,
            'allocation_pools': [
                {
                    'start': '10.10.11.33',
                    'end': '10.10.11.55'
                }
            ],
            'dns_nameservers': ['10.10.11.22', '10.10.11.23'],
            'host_routes': [
                {
                    'nexthop': '10.10.11.1',
                    'destination': '1.1.1.0/24'
                }
            ]
        }

        q_subnet = self.q_create_subnet(**subnet)

        sub = self._get_subnet_from_network(q_subnet['subnet']['id'],
                                            self.test_network['network']['id'])
        self.assertIsNotNone(sub)

        self.q_delete_subnet(q_subnet)
        sub = self._get_subnet_from_network(q_subnet['subnet']['id'],
                                            self.test_network['network']['id'])
        self.assertIsNone(sub)

    def _get_subnet_from_network(self, subnet_id, network_id):
        tf_network = self.tf_get('virtual-network', network_id)
        ipam_refs = tf_network.get_network_ipam_refs()

        self.assertIsNotNone(ipam_refs)

        for ref in ipam_refs:
            subnets = ref.get('attr').ipam_subnets or ()
            for sub in subnets:
                if uuid.UUID(subnet_id) == uuid.UUID(sub.get_subnet_uuid()):
                    return sub
        return None
