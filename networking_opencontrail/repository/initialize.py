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
from functools import wraps

from requests.exceptions import ConnectionError

from networking_opencontrail.common.utils import register_vnc_api_options
from networking_opencontrail.repository.client import tf_client
from networking_opencontrail.repository.tag import ml2_tag_manager


def initialize():
    register_vnc_api_options()


def connect():
    """Create new API session

    Performs steps required to ensure connection and necessary post
    connection setup.
    """

    if tf_client.connected:
        return

    tf_client.connect()
    ml2_tag_manager.initialize()


def reconnect(fun):
    """Decorator used to ensure connection is created before call"""

    @wraps(fun)
    def wrapper(*args, **kwargs):
        try:
            connect()
        except ConnectionError:
            # Rewrite exception with own message, as it's most likely clear
            # what happened at this point.
            raise ConnectionError(
                "Could not connect to Contrail, check plugin configuration")

        return fun(*args, **kwargs)

    return wrapper
