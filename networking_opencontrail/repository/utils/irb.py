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

from oslo_log import log as logging

RB_GATEWAY_ROLES = ["crb-gateway", "crb-mcast-gateway", "erb-ucast-gateway"]
"""
In TF exist also 'dc-gateway' and 'dci-gateway' roles,
but this plugin assigns to Logical Router only devices
with CRB or ERB specific gateway roles.
"""

LOG = logging.getLogger(__name__)


def select_physical_routers_for_irb(physical_routers):
    """Selects physical routers for IRB placing on them.

    Firstly excludes physical routers without assigned physical
    and overlay role. Then selects routers with assigned one of gateway roles.

    :param physical_routers:
    :type: initial list of physical routers
    :return: list of physical routers for IRB placing on them
    :rtype: list
    """
    physical_routers = exclude_without_assigned_roles(physical_routers)
    return exclude_without_gateway_role(physical_routers)


def exclude_without_assigned_roles(physical_routers):
    return [
        pr for pr in physical_routers if has_assigned_roles(pr)
    ]


def has_assigned_roles(physical_router):
    return (physical_router.get_physical_role_refs() is not None
            and physical_router.get_overlay_role_refs() is not None)


def exclude_without_gateway_role(physical_routers):
    return [
        pr for pr in physical_routers if has_gateway_role(pr)
    ]


def has_gateway_role(physical_router):
    overlay_role_names = [
        ref["to"][-1] for ref in physical_router.get_overlay_role_refs()
    ]
    return any(role in RB_GATEWAY_ROLES for role in overlay_role_names)
