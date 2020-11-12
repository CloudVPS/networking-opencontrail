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

from networking_opencontrail.sync.synchronizers import NetworkSynchronizer
from networking_opencontrail.tests import base


class NetworkSynchronizerTestCase(base.TestCase):
    def setUp(self):
        super(NetworkSynchronizerTestCase, self).setUp()

    @mock.patch(
        "networking_opencontrail.neutron.neutron_client.directory.get_plugin"
    )
    @mock.patch("networking_opencontrail.sync.synchronizers.repository")
    def test_calculate_diff(self, repository, core_plugin):
        # Exists both in Neutron and TF config API.
        q_network_1 = {
            "id": "net-id-1",
            "name": "",
            "fq_name": ["", "", ""]
        }
        # Doesn't exist in TF config API - should be created.
        q_network_2 = {
            "id": "net-id-2",
            "name": "",
            "fq_name": ["", "", ""]
        }
        # Used for SNAT - should be ignored.
        q_network_snat = {
            "id": "net-id-snat",
            "name": "net_snat_",
            "fq_name": ["", "", "net_snat_"],
        }

        # Represents q_network_1 in TF config API.
        tf_network_1 = {
            "fq_name": ["default-domain", "test-project", "net-1"],
            "uuid": "net-id-1",
        }
        # TF only - should be deleted.
        tf_network_3 = {
            "fq_name": ["default-domain", "test-project", "net-3"],
            "uuid": "net-id-3",
        }
        # Has default-project as parent - should be ignored
        tf_network_ignore = {
            "fq_name": ["default-domain", "default-project", "net-4"],
            "uuid": "net-id-4",
        }

        core_plugin.return_value.get_networks.return_value = [
            q_network_1,
            q_network_2,
            q_network_snat,
        ]
        repository.tf_client.list_networks.return_value = [
            tf_network_1,
            tf_network_3,
            tf_network_ignore,
        ]

        synchronizer = NetworkSynchronizer()
        to_create = synchronizer.calculate_create_diff()
        to_delete = synchronizer.calculate_delete_diff()

        self.assertEqual([q_network_2], to_create)
        self.assertEqual([tf_network_3], to_delete)
