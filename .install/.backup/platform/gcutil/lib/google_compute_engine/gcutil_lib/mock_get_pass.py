# Copyright 2013 Google Inc. All Rights Reserved.
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

"""Helper class to mock getpass.getpass with context management."""

import getpass


class MockGetPass(object):

  def __init__(self, getpass_call):
    self._new_getpass = getpass_call

  def __enter__(self):
    self._original_getpass = getpass.getpass
    getpass.getpass = self._new_getpass
    return self

  def __exit__(self, the_type, value, traceback):
    getpass.getpass = self._original_getpass
