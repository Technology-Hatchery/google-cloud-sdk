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

"""Helper module to manage initial password for Windows images."""

import getpass

from gcutil_lib import gcutil_errors
from gcutil_lib import gcutil_logging

LOGGER = gcutil_logging.LOGGER

GCE_ADMIN_ACCOUNT = 'gceadmin'
MIN_PASSWORD_LENGTH = 8
NON_ALPHA_NUM_CHARS = '~!@#$%^&*_-+=`|\\(){}[]:;"\'<>,.?/'
MIN_CHAR_CATEGORIES = 3


def GetPassword(prompt):
  """Prompts and gets the initial windows password from user.

  Args:
    prompt: The prompt for the user.

  Returns:
    The password user typed.

  Raises:
    CommandError: The user typed in weak or mismatched password and we have
      exhausted the retries.
  """
  max_attempt_count = 3
  for i in xrange(max_attempt_count):
    password1 = getpass.getpass(prompt)
    password2 = getpass.getpass('Please retype the password')
    if password1 == password2:
      try:
        ValidateStrongPasswordRequirement(password1)
        return password1
      except gcutil_errors.CommandError as e:
        error_message = e.message
    else:
      error_message = 'Passwords do not match.'
    if i < max_attempt_count - 1:
      error_message += ' Try again.'
      LOGGER.warn(error_message)
  raise gcutil_errors.CommandError(error_message)


def ValidateStrongPasswordRequirement(password):
  """Validates that a password meets strong password requirement.

  The strong password must be at least 8 chars long and meet the
  Windows password complexity requirement documented at
  http://technet.microsoft.com/en-us/library/cc786468(v=ws.10).aspx

  Args:
    password: Password to be validated.

  Raises:
    CommandError: The password does not meet the strong password requirement.
  """
  if not password or len(password) < MIN_PASSWORD_LENGTH:
    raise gcutil_errors.CommandError(
        'Windows password must be at least %d characters long.' %
        MIN_PASSWORD_LENGTH)

  categories = 0
  uppercase = False
  lowercase = False
  digit = False
  nonalphanum = False
  alpha = False
  for x in password:
    if x.isupper():
      uppercase = True
    elif x.islower():
      lowercase = True
    elif x.isdigit():
      digit = True
    elif x in NON_ALPHA_NUM_CHARS:
      nonalphanum = True
    elif x.isalpha():
      alpha = True
    categories = uppercase + lowercase + digit + nonalphanum + alpha
    if categories >= MIN_CHAR_CATEGORIES:
      break
  if categories < MIN_CHAR_CATEGORIES:
    raise gcutil_errors.CommandError(
        'Windows password must contain at least 3 types of characters. See '
        'http://technet.microsoft.com/en-us/library/cc786468(v=ws.10).aspx')

  # Currently we only support 'gceadmin' account, and it does not have
  # display name, so we only need to check against string 'gceadmin'
  if GCE_ADMIN_ACCOUNT in password.lower():
    raise gcutil_errors.CommandError(
        'Windows password cannot contain the user account name: %s.' %
        GCE_ADMIN_ACCOUNT)
