# Copyright 2012 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Unit tests for the windows_password module."""

import path_initializer
path_initializer.InitSysPath()

import re

import unittest

from gcutil_lib import gcutil_errors
from gcutil_lib import mock_get_pass
from gcutil_lib import windows_password


class WindowsPasswordTest(unittest.TestCase):

  def testGetPasswordMismatch(self):
    num_getpass_calls = [0]
    mismatch_round = 2
    strong_password = '!password1'
    def _GetPassMismatch(_):
      num_getpass_calls[0] += 1
      if (num_getpass_calls[0] - 1) // 2 < mismatch_round:
        return 'password0' if num_getpass_calls[0] % 2 == 0 else 'password1'
      else:
        return strong_password

    with mock_get_pass.MockGetPass(_GetPassMismatch):
      password = windows_password.GetPassword('type password')
      self.assertEquals(strong_password, password)
      self.assertEquals((mismatch_round + 1) * 2, num_getpass_calls[0])

    num_getpass_calls = [0]
    mismatch_round = 3
    with mock_get_pass.MockGetPass(_GetPassMismatch):
      self._AssertGetPasswordErrorMessageMatchesPattern(
          'Passwords do not match')

  def testGetPasswordWeakPassword(self):
    weak_round = 2
    num_getpass_calls = [0]
    strong_password = '!password1'

    def _GetPassWeakPassword(_):
      num_getpass_calls[0] += 1
      if (num_getpass_calls[0] - 1) // 2 < weak_round:
        return 'weak_password'
      else:
        return strong_password
    with mock_get_pass.MockGetPass(_GetPassWeakPassword):
      password = windows_password.GetPassword('type password')
      self.assertEquals(strong_password, password)
      self.assertEquals((weak_round + 1) * 2, num_getpass_calls[0])

    num_getpass_calls = [0]
    weak_round = 3
    with mock_get_pass.MockGetPass(_GetPassWeakPassword):
      self._AssertGetPasswordErrorMessageMatchesPattern(
          'must contain at least 3 types of characters')

  def _AssertGetPasswordErrorMessageMatchesPattern(self, error_message_pattern):
    try:
      windows_password.GetPassword('type password')
      self.fail('No exception thrown')
    except gcutil_errors.CommandError as e:
      self.assertFalse(re.search(error_message_pattern, e.message) is None)

  def testValidateStrongPasswordRequirement(self):

    def _AssertErrorMessageMatchesPattern(password, error_message_pattern):
      try:
        windows_password.ValidateStrongPasswordRequirement(
            password)
        self.fail('No exception thrown')
      except gcutil_errors.CommandError as e:
        self.assertFalse(re.search(error_message_pattern, e.message) is None)

    # Password too short
    regexp = r'must be at least \d+ characters long'
    _AssertErrorMessageMatchesPattern('!Ab1234', regexp)

    # Password does not contain enough categories of chars
    regexp = 'must contain at least 3 types of characters'
    _AssertErrorMessageMatchesPattern('a1234567', regexp)
    _AssertErrorMessageMatchesPattern('Aabcdefg', regexp)
    _AssertErrorMessageMatchesPattern('!abcdefg', regexp)
    _AssertErrorMessageMatchesPattern('!1234567', regexp)

    # Password contains 'gceadmin' account name
    regexp = 'cannot contain the user account name'
    _AssertErrorMessageMatchesPattern('Ab1GceAdmin!', regexp)


if __name__ == '__main__':
  unittest.main()
