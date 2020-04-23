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


class SubnetResourceTestCase(base.TestCase):

    def test_create_from_q_subnet(self):
        q_subnet = {
            "id": "fadffa22-3022-4bdb-9045-0b5de8901d3c",
            "name": "test_subnet",
            "cidr": "10.10.11.0/24",
            "gateway_ip": "10.10.11.1",
            "ip_version": 4,
        }

        ipam_subnet = create(q_subnet=q_subnet)

        self.assertEqual(ipam_subnet.subnet_uuid, q_subnet["id"])
        self.assertEqual(ipam_subnet.subnet_name, q_subnet["name"])
        self.assertEqual(ipam_subnet.default_gateway, q_subnet["gateway_ip"])
        subnet = ipam_subnet.get_subnet()
        self.assertEqual(subnet.ip_prefix, "10.10.11.0")
        self.assertEqual(subnet.ip_prefix_len, 24)
