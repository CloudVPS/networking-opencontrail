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

from oslo_config import cfg
from vnc_api import vnc_api

VALUE = '__ML2__'
TYPE = 'label'
NAME = '{}={}'.format(TYPE, VALUE)
FQ_NAME = [NAME]


def assign_to_ntf(obj):
    """Adds a special NTF tag to Tungsten Fabric object"""
    obj.add_tag(identifier_tag())


def belongs_to_ntf(obj):
    """Returns true if the object was created by the NTF"""
    return is_tagged(obj, NAME)


def identifier_tag():
    """Returns tag object used to assign object to NTF"""
    return vnc_api.Tag(
        tag_value=VALUE,
        tag_type_name=TYPE,
        name=NAME,
        fq_name=FQ_NAME,
    )


def is_tagged(resource, tag):
    """Check if tag is in resource"""
    try:
        tag_refs = resource.get_tag_refs() or ()
    except AttributeError:
        tag_refs = resource.get('tag_refs', ())
    return tag in {ref['to'][-1] for ref in tag_refs}


def is_management_port(port):
    """Checks if port instance does not contain management port indication tag.

    The list of ports should be defined in configuration, using
    APISERVER.management_port_tags option.

    """
    management_tag_names = cfg.CONF.APISERVER.management_port_tags
    return check_tags_on_resource(port, management_tag_names)


def is_data_port(port, tag_name):
    """Checks if port instance does contain data port tag provided."""
    tag = '{}={}'.format(TYPE, tag_name)
    return is_tagged(port, tag)


def check_tags_on_resource(resource, tag_names):
    """Check if resource has any of tags from provided list."""
    try:
        tag_refs = resource.get_tag_refs() or ()
    except AttributeError:
        tag_refs = resource.get('tag_refs', ())
    resource_tags = {ref['to'][-1] for ref in tag_refs}

    tags = set(
        '{}={}'.format(TYPE, value)
        for value in tag_names
    )

    return bool(resource_tags & tags)
