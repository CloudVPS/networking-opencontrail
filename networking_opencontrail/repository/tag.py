# Copyright (c) 2019 OpenStack Foundation
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

from oslo_log import log as logging
from vnc_api import vnc_api

from networking_opencontrail.repository.client import tf_client


LOG = logging.getLogger(__name__)


class Ml2TagManager(object):
    TAG_VALUE = u'__ML2__'
    TAG_TYPE_VALUE = u'label'
    NAME = u'{}={}'.format(TAG_TYPE_VALUE, TAG_VALUE)
    FQ_NAME = [NAME]

    ml2_tag = None

    @classmethod
    def initialize(cls):
        existing_ml2_tag = tf_client.read_tag(fq_name=cls.FQ_NAME)

        if existing_ml2_tag:
            cls.ml2_tag = existing_ml2_tag
        else:
            new_ml2_tag = vnc_api.Tag(
                tag_value=cls.TAG_VALUE,
                tag_type_name=cls.TAG_TYPE_VALUE,
                name=cls.NAME,
                fq_name=cls.FQ_NAME
            )
            tf_client.create_tag(new_ml2_tag)
            cls.ml2_tag = new_ml2_tag

    def tag(self, obj):
        return obj.add_tag(self.ml2_tag)

    def check(self, obj):
        tag_refs = obj.get_tag_refs() or ()
        tag_fq_names = [ref['to'] for ref in tag_refs]
        return self.FQ_NAME in tag_fq_names

ml2_tag_manager = Ml2TagManager()
