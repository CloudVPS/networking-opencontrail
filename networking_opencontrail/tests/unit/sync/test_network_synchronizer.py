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
import mock

from networking_opencontrail.sync.synchronizer import NetworkSynchronizer
from networking_opencontrail.tests import base


class NetworkConverterTestCase(base.TestCase):
    def setUp(self):
        super(NetworkConverterTestCase, self).setUp()
        self.tf_driver = mock.Mock()

    @mock.patch(
        "networking_opencontrail.sync.synchronizer.directory.get_plugin"
    )
    def test_calculate_diff(self, core_plugin):
        network_1 = {"id": "net-id-1", "name": "", "fq_name": ["", "", ""]}
        network_2 = {"id": "net-id-2", "name": "", "fq_name": ["", "", ""]}
        network_3 = {"id": "net-id-3", "name": "", "fq_name": ["", "", ""]}
        network_4 = {
            "id": "net-id-4",
            "name": "",
            "fq_name": ["", "default-project", ""],
        }
        network_5 = {
            "id": "net-id-5",
            "name": "net_snat_5",
            "fq_name": ["", "", ""],
        }

        self.tf_driver.get_networks.return_value = [
            network_1,
            network_2,
            network_4,
        ]
        core_plugin.return_value.get_networks.return_value = [
            network_1,
            network_3,
            network_5,
        ]

        synchronizer = NetworkSynchronizer(self.tf_driver)
        synchronizer.calculate_diff()

        self.assertEqual([network_3], synchronizer.to_create)
        self.assertEqual([network_2], synchronizer.to_delete)
