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

from base64 import b64decode
from base64 import b64encode
import uuid


sriov_compute = 'sriov-compute'
ovs_compute = 'ovs-compute'
baremetal = 'baremetal'


def is_sriov_node(node):
    """Determine if node uses sriov data ports."""
    return node.node_type == sriov_compute


def first(iterable, condition=lambda x: True, default=None):
    return next(
        (x for x in iterable if condition(x)), default)


def make_uuid(name):
    return str(uuid.uuid3(uuid.NAMESPACE_DNS, str(name)))


def standardize_name(name):
    """Standardize name to allow full charset available in OpenStack.

    Code logic relies on some special characters in the resource's name.
    """
    encoded = name.encode('ascii')
    standardized = b64encode(encoded)
    return standardized.decode('ascii')


def destandardize_name(name):
    """Destandardize previously encoded name."""
    encoded = name.encode('ascii')
    destandardized = b64decode(encoded)
    return destandardized.decode('ascii')
