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

from vnc_api import vnc_api

from networking_opencontrail.repository.utils.irb import \
    select_physical_routers_for_irb
from networking_opencontrail.tests import base


class FindPRForIRBTestCase(base.TestCase):
    """Following scenarios are tested:

    1. Selecting all spine switches for CRB case
    2. Selecting all leaf switches for ERB case
    3. Exclude from consideration switches without assigned roles
    """
    def setUp(self):
        super(FindPRForIRBTestCase, self).setUp()
        self.spine_role = vnc_api.PhysicalRole(name="spine")
        self.leaf_role = vnc_api.PhysicalRole(name="leaf")
        self.crb_access = vnc_api.OverlayRole(name="crb-access")
        self.crb_gateway = vnc_api.OverlayRole(name="crb-gateway")
        self.erb_ucast_gateway = vnc_api.OverlayRole(name="erb-ucast-gateway")
        self.route_reflector = vnc_api.OverlayRole(name="route-reflector")

    @classmethod
    def create_physical_router(cls, name, physical_role, overlay_roles):
        physical_router = vnc_api.PhysicalRouter(name=name)
        physical_router.add_physical_role(physical_role)
        for overlay_role in overlay_roles:
            physical_router.add_overlay_role(overlay_role)
        return physical_router

    def test_select_physical_routers_crb(self):
        spine_1 = self.create_physical_router(
            name="qfx-spine-1",
            physical_role=self.spine_role,
            overlay_roles=[self.route_reflector, self.crb_gateway]
        )

        spine_2 = self.create_physical_router(
            name="qfx-spine-2",
            physical_role=self.spine_role,
            overlay_roles=[self.route_reflector, self.crb_gateway]
        )

        leaf_1 = self.create_physical_router(
            name="qfx-leaf-1",
            physical_role=self.leaf_role,
            overlay_roles=[self.crb_access]
        )

        leaf_2 = self.create_physical_router(
            name="qfx-leaf-2",
            physical_role=self.leaf_role,
            overlay_roles=[self.crb_access]
        )

        routers = [leaf_1, leaf_2, spine_1, spine_2]
        result = set(select_physical_routers_for_irb(routers))
        expected = {spine_1, spine_2}

        self.assertEqual(result, expected)

    def test_select_physical_routers_erb(self):
        spine_1 = self.create_physical_router(
            name="qfx-spine",
            physical_role=self.spine_role,
            overlay_roles=[self.route_reflector]
        )

        leaf_1 = self.create_physical_router(
            name="qfx-leaf-1",
            physical_role=self.leaf_role,
            overlay_roles=[self.erb_ucast_gateway]
        )

        leaf_2 = self.create_physical_router(
            name="qfx-leaf-2",
            physical_role=self.leaf_role,
            overlay_roles=[self.erb_ucast_gateway]
        )

        routers = [leaf_1, leaf_2, spine_1]
        result = set(select_physical_routers_for_irb(routers))
        expected = {leaf_1, leaf_2}

        self.assertEqual(result, expected)

    def test_select_physical_routers_exclude_invalid(self):
        spine_1 = self.create_physical_router(
            name="qfx-spine-1",
            physical_role=self.spine_role,
            overlay_roles=[self.route_reflector, self.crb_gateway]
        )

        leaf_1 = self.create_physical_router(
            name="qfx-leaf-1",
            physical_role=self.leaf_role,
            overlay_roles=[self.crb_access]
        )

        leaf_2 = self.create_physical_router(
            name="qfx-leaf-2",
            physical_role=self.leaf_role,
            overlay_roles=[self.crb_access]
        )

        without_roles = vnc_api.PhysicalRouter(name='without_roles')

        routers = [leaf_1, leaf_2, spine_1, without_roles]
        result = set(select_physical_routers_for_irb(routers))
        expected = {spine_1}

        self.assertEqual(result, expected)
