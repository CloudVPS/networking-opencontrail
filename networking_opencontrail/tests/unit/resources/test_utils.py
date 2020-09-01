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
import ddt

from networking_opencontrail.tests import base

from networking_opencontrail.resources.utils import destandardize_name
from networking_opencontrail.resources.utils import standardize_name


@ddt.ddt
class UtilsResourceTestCase(base.TestCase):
    def test_standarize_name(self):
        test_name = "test-name-with-#-1"
        s_test_name = standardize_name(test_name)

        self.assertEqual(destandardize_name(s_test_name), "test-name-with-#-1")
