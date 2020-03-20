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

from networking_opencontrail.repository.utils.tag import ml2_tag_manager
from networking_opencontrail.tests import base

from vnc_api import vnc_api


class TagManagerTestCase(base.TestCase):

    @mock.patch("networking_opencontrail.repository.utils.tag.tf_client")
    def test_check_tag(self, tf_client):
        tf_client.read_tag.return_value = None

        dummy_tag = vnc_api.Tag(name='dummy_tag')
        network_1 = vnc_api.VirtualNetwork()
        network_2 = vnc_api.VirtualNetwork()
        network_3 = vnc_api.VirtualNetwork()

        ml2_tag_manager.initialize()
        ml2_tag_manager.tag(network_1)
        network_2.add_tag(dummy_tag)

        self.assertTrue(ml2_tag_manager.check(network_1))
        self.assertFalse(ml2_tag_manager.check(network_2))
        self.assertFalse(ml2_tag_manager.check(network_3))
