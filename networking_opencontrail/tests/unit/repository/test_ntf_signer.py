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

from networking_opencontrail.repository.utils import tagger
from networking_opencontrail.tests import base


class NTFSignerTest(base.TestCase):
    def test_properly_assigned_resource(self):
        network = vnc_api.VirtualNetwork()
        tagger.assign_to_ntf(network)
        self.assertTrue(tagger.belongs_to_ntf(network))

    def test_unassigned_resource(self):
        network = vnc_api.VirtualNetwork()
        self.assertFalse(tagger.belongs_to_ntf(network))

    def test_identifier_tag(self):
        network = vnc_api.VirtualNetwork()
        network.add_tag(tagger.identifier_tag())
        self.assertTrue(tagger.belongs_to_ntf(network))

    def test_invalid_tag(self):
        network = vnc_api.VirtualNetwork()
        network.add_tag(vnc_api.Tag(name='dummy_tag'))
        self.assertFalse(tagger.belongs_to_ntf(network))

    @mock.patch("networking_opencontrail.repository.utils.tagger.cfg")
    def test_dataport_validation_without_tag_when_undefined(self, cfg):
        cfg.CONF.APISERVER.management_port_tags = []
        port = vnc_api.Port()
        self.assertTrue(tagger.verify_data_port(port))

    @mock.patch("networking_opencontrail.repository.utils.tagger.cfg")
    def test_dataport_validation_without_tag_when_defined(self, cfg):
        cfg.CONF.APISERVER.management_port_tags = ['tag']
        port = vnc_api.Port()
        self.assertTrue(tagger.verify_data_port(port))

    @mock.patch("networking_opencontrail.repository.utils.tagger.cfg")
    def test_dataport_validation_with_tag_not_matched(self, cfg):
        cfg.CONF.APISERVER.management_port_tags = ['tag']
        port = vnc_api.Port()
        port.add_tag(vnc_api.Tag(name='dummy_tag'))
        self.assertTrue(tagger.verify_data_port(port))

    @mock.patch("networking_opencontrail.repository.utils.tagger.cfg")
    def test_dataport_validation_with_tag_matched(self, cfg):
        cfg.CONF.APISERVER.management_port_tags = ['tag']
        port = vnc_api.Port()
        name = '{}={}'.format(tagger.TYPE, 'tag')
        port.add_tag(
            vnc_api.Tag(
                tag_value='tag',
                tag_type_name=tagger.TYPE,
                name=name,
                fq_name=[name],
            )
        )
        self.assertFalse(tagger.verify_data_port(port))
