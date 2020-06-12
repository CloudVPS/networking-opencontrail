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

from networking_opencontrail.resources.subnet import create
from networking_opencontrail.resources.subnet import get_dhcp_option_list
from networking_opencontrail.resources.subnet import get_dhcp_option_type
from networking_opencontrail.resources.subnet import get_host_routes
from networking_opencontrail.resources.subnet import get_host_routes_type


class SubnetResourceTestCase(base.TestCase):

    def test_create_from_q_subnet(self):
        q_subnet = {
            "id": "fadffa22-3022-4bdb-9045-0b5de8901d3c",
            "name": "test_subnet",
            "cidr": "10.10.11.0/24",
            "gateway_ip": "10.10.11.1",
            "ip_version": 4,
            "dns_nameservers": [],
            "host_routes": []
        }

        ipam_subnet = create(q_subnet=q_subnet)

        self.assertEqual(ipam_subnet.subnet_uuid, q_subnet["id"])
        self.assertEqual(ipam_subnet.subnet_name, q_subnet["name"])
        self.assertEqual(ipam_subnet.default_gateway, q_subnet["gateway_ip"])
        subnet = ipam_subnet.get_subnet()
        self.assertEqual(subnet.ip_prefix, "10.10.11.0")
        self.assertEqual(subnet.ip_prefix_len, 24)

    def test_get_dhcp_option_list(self):
        dns_nameservers = ['10.10.172.22', '10.10.172.44']
        dhcp_option_list = get_dhcp_option_list(dns_nameservers)
        dhcp_option_name = dhcp_option_list.dhcp_option[0].dhcp_option_name
        dhcp_option_value = dhcp_option_list.dhcp_option[0].dhcp_option_value
        self.assertEqual(dhcp_option_name, "6")
        self.assertEqual(dhcp_option_value, "10.10.172.22 10.10.172.44")

    def test_get_dhcp_option_list_empty_dns(self):
        dns_nameservers = []
        dhcp_option_list = get_dhcp_option_list(dns_nameservers)
        self.assertIsNone(dhcp_option_list)

    def test_get_host_route_type(self):
        host_routes = [{'nexthop': '10.10.172.1', 'destination': '1.1.1.0/24'}]
        host_route_type = get_host_routes_type(host_routes)
        prefix = host_route_type[0].prefix
        next_hop = host_route_type[0].next_hop
        self.assertEqual(prefix, "1.1.1.0/24")
        self.assertEqual(next_hop, "10.10.172.1")

    def test_get_host_route_type_empty_host_route(self):
        host_routes = []
        host_route_type = get_host_routes_type(host_routes)
        self.assertEqual(host_route_type, [])

    def test_get_host_routes(self):
        gw = '10.10.190.1'
        dest = '1.1.1.0/24'
        host_routes_config = [{'nexthop': gw, 'destination': dest}]
        host_routes = get_host_routes(host_routes_config)
        prefix = host_routes.route[0].prefix
        next_hop = host_routes.route[0].next_hop
        self.assertEqual(prefix, "1.1.1.0/24")
        self.assertEqual(next_hop, "10.10.190.1")

    def test_get_host_routes_empty_host_routes(self):
        host_routes_config = []
        host_routes = get_host_routes(host_routes_config)
        self.assertIsNone(host_routes)

    def test_get_dhcp_option_type(self):
        dns_servers = "10.10.31.22 10.10.31.23"
        dhcp_option_type = get_dhcp_option_type(dns_servers)
        dhcp_option_name = dhcp_option_type.dhcp_option_name
        dhcp_option_value = dhcp_option_type.dhcp_option_value
        self.assertEqual(dhcp_option_name, "6")
        self.assertEqual(dhcp_option_value, "10.10.31.22 10.10.31.23")

    def test_get_dhcp_option_type_empty_dns(self):
        dns_servers = ""
        dhcp_option_type = get_dhcp_option_type(dns_servers)
        dhcp_option_name = dhcp_option_type.dhcp_option_name
        dhcp_option_value = dhcp_option_type.dhcp_option_value
        self.assertEqual(dhcp_option_name, "6")
        self.assertEqual(dhcp_option_value, "")
