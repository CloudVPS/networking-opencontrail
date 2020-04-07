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
from vnc_api import vnc_api

from networking_opencontrail.sync.synchronizers import NetworkSynchronizer
from networking_opencontrail.tests import base


class NetworkSynchronizerTestCase(base.TestCase):
    def setUp(self):
        super(NetworkSynchronizerTestCase, self).setUp()

    @mock.patch("networking_opencontrail.sync.base.repository.ml2_tag_manager")
    @mock.patch("networking_opencontrail.sync.base.directory.get_plugin")
    @mock.patch("networking_opencontrail.sync.synchronizers.repository")
    def test_calculate_diff(self, repository, core_plugin, ml2_tag_manager):
        # Exists both in Neutron and TF config API.
        n_network_1 = {
            "id": "net-id-1",
            "name": "",
            "fq_name": ["", "", ""]
        }
        # Doesn't exist in TF config API - should be created.
        n_network_2 = {
            "id": "net-id-2",
            "name": "",
            "fq_name": ["", "", ""]
        }
        # Used for SNAT - should be ignored.
        n_network_snat = {
            "id": "net-id-snat",
            "name": "net_snat_",
            "fq_name": ["", "", "net_snat_"],
        }
        project = vnc_api.Project(name="test-project")

        # Represents n_network_1 in TF config API.
        tf_network_1 = vnc_api.VirtualNetwork(name="net-1",
                                              parent_obj=project)
        tf_network_1.set_uuid("net-id-1")

        # TF only - should be deleted.
        tf_network_3 = vnc_api.VirtualNetwork(name="net-3",
                                              parent_obj=project)
        tf_network_3.set_uuid("net-id-3")

        # Has default-project as parent - should be ignored
        tf_network_ignore = vnc_api.VirtualNetwork(name="net-4")
        tf_network_ignore.set_uuid("net-id-4")

        # Simulating no ML2 tag - should be ignored
        tf_network_no_tag = vnc_api.VirtualNetwork(name="net-4",
                                                   parent_obj=project)
        tf_network_no_tag.set_uuid("net-id-5")
        ml2_tag_manager.check.side_effect = lambda x: x.name != "net-4"

        core_plugin.return_value.get_networks.return_value = [
            n_network_1,
            n_network_2,
            n_network_snat,
        ]
        repository.tf_client.list_networks.return_value = [
            tf_network_1,
            tf_network_3,
            tf_network_ignore,
            tf_network_no_tag,
        ]

        synchronizer = NetworkSynchronizer()
        synchronizer.calculate_diff()

        self.assertEqual([n_network_2], synchronizer.to_create)
        self.assertEqual([tf_network_3], synchronizer.to_delete)
