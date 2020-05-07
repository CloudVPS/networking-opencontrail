# Copyright (c) 2017 OpenStack Foundation
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
import logging

import ddt
import mock

from networking_opencontrail.l3.service_provider import validate_flavor
from neutron.tests.unit.extensions import base as test_extensions_base


@ddt.ddt
class L3FlavorValidatorTestCases(test_extensions_base.ExtensionTestCase):
    """L3 Flavor Validation test cases.

    Consists of following cases:
        1. Return True if router has the expected flavor ID
        2. Return False if router has different flavor ID than expected
        3. Return False if router has no flavor ID
    """
    def setUp(self):
        super(L3FlavorValidatorTestCases, self).setUp()
        self.provider_name = 'test-provider-name'
        self.flavor_id = 'test-flavor-id'
        self.context = mock.Mock()

        self.fl_plugin = mock.Mock()
        self.fl_plugin.get_flavor_next_provider = self.get_flavor_next_provider

    def tearDown(self):
        super(L3FlavorValidatorTestCases, self).tearDown()
        logging.disable(logging.NOTSET)

    @mock.patch(
        'networking_opencontrail.l3.service_provider.directory.get_plugin')
    def test_validate(self, get_plugin):
        get_plugin.return_value = self.fl_plugin
        router = {"flavor_id": self.flavor_id}

        validation_result = validate_flavor(
            self.provider_name, router, self.context)

        self.assertTrue(validation_result)

    @ddt.data(
        ('123', False),
        (None, False),
    )
    @ddt.unpack
    @mock.patch(
        'networking_opencontrail.l3.service_provider.directory.get_plugin')
    def test_validate_false(self, flavor_id, expected, get_plugin):
        get_plugin.return_value = self.fl_plugin
        router = {"flavor_id": flavor_id}

        validation_result = validate_flavor(
            self.provider_name, router, self.context)

        self.assertEqual(expected, validation_result)

    def get_flavor_next_provider(self, context, flavor_id):
        """Returns flavor provider data based on flavor_id parameter."""
        if flavor_id == self.flavor_id:
            flavor_provider = {'driver': self.provider_name}
        else:
            flavor_provider = {'driver': 'not-our-provider'}
        return [flavor_provider]
