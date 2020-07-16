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
from networking_opencontrail.repository.utils.utils import is_port_managed
from networking_opencontrail.tests import base


class NTFSignerTest(base.TestCase):
    @mock.patch("networking_opencontrail.repository.utils.tagger.cfg")
    def test_is_port_managed_when_ovs_and_untagged(self, cfg):
        cfg.CONF.APISERVER.management_port_tags = []
        node = vnc_api.Node(name="node")
        node.node_type = 'ovs-compute'
        port = vnc_api.Port()
        self.assertTrue(is_port_managed(node, port))

    @mock.patch("networking_opencontrail.repository.utils.tagger.cfg")
    def test_is_port_managed_when_ovs_and_management(self, cfg):
        cfg.CONF.APISERVER.management_port_tags = ['tag']
        node = vnc_api.Node(name="node")
        node.node_type = 'ovs-compute'
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
        self.assertFalse(is_port_managed(node, port))

    @mock.patch("networking_opencontrail.repository.utils.tagger.cfg")
    def test_is_port_managed_when_ovs_and_data(self, cfg):
        cfg.CONF.APISERVER.data_port_tags = ['tag']
        node = vnc_api.Node(name="node")
        node.node_type = 'ovs-compute'
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
        self.assertTrue(is_port_managed(node, port))

    @mock.patch("networking_opencontrail.repository.utils.tagger.cfg")
    def test_is_port_managed_when_sriov_and_untagged(self, cfg):
        cfg.CONF.APISERVER.management_port_tags = ['tag']
        node = vnc_api.Node(name="node")
        node.node_type = 'sriov-compute'
        port = vnc_api.Port()
        self.assertTrue(is_port_managed(node, port))

    @mock.patch("networking_opencontrail.repository.utils.tagger.cfg")
    def test_is_port_managed_when_sriov_and_management(self, cfg):
        cfg.CONF.APISERVER.management_port_tags = ['tag']
        node = vnc_api.Node(name="node")
        node.node_type = 'sriov-compute'
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
        self.assertFalse(is_port_managed(node, port))

    @mock.patch("networking_opencontrail.repository.utils.tagger.cfg")
    def test_is_port_managed_when_sriov_and_data(self, cfg):
        cfg.CONF.APISERVER.data_port_tags = ['tag']
        node = vnc_api.Node(name="node")
        node.node_type = 'sriov-compute'
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
        self.assertFalse(is_port_managed(node, port))
