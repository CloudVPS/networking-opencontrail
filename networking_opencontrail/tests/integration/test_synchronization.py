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

from retrying import retry

from networking_opencontrail.tests.base import IntegrationTestCase

from vnc_api import vnc_api


def retry_if_none(result):
    return result is None


def retry_if_not_none(result):
    return result is not None


class TestNetworkSynchronization(IntegrationTestCase):
    def setUp(self):
        super(TestNetworkSynchronization, self).setUp()

        self.ml2_tag = self.tf_list(
            'tag', detail=True, fq_names=[["label=__ML2__"]]
        )[0]

    def test_network_recreate(self):
        net = {
            "name": "test_vlan_network",
            "provider:network_type": "vlan",
            'provider:segmentation_id': 20,
            "provider:physical_network": self.provider,
            "admin_state_up": True,
        }
        q_net = self.q_create_network(**net)

        self.tf_delete("virtual-network", q_net["network"]["id"])

        self.assertIsNotNone(
            self._get_recreated_resource(
                "virtual-network", q_net["network"]["id"]
            )
        )

    def test_network_redelete(self):
        network_1 = vnc_api.VirtualNetwork(
            name="test_network_1", parent_obj=self.tf_project
        )
        network_2 = vnc_api.VirtualNetwork(
            name="test_network_2", parent_obj=self.tf_project
        )

        network_1.add_tag(self.ml2_tag)

        network_1_uuid = self.tf_create(network_1)
        network_2_uuid = self.tf_create(network_2)

        self.assertIsNone(
            self._get_redeleted_resource("virtual-network", network_1_uuid)
        )
        self.assertIsNotNone(self.tf_get("virtual-network", network_2_uuid))

    @retry(
        retry_on_result=retry_if_none,
        wait_fixed=1000,
        stop_max_delay=10000
    )
    def _get_recreated_resource(self, res_type, res_id):
        return self.tf_get(res_type, res_id)

    @retry(
        retry_on_result=retry_if_not_none,
        wait_fixed=1000,
        stop_max_delay=10000,
    )
    def _get_redeleted_resource(self, res_type, res_id):
        return self.tf_get(res_type, res_id)
