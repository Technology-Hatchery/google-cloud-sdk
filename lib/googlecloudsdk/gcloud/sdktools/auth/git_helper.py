# Copyright 2013 Google Inc. All Rights Reserved.

"""A git credential helper that provides Google git repository passwords.

Reads a session from stdin that looks a lot like:
  protocol=https
  host=code.google.com
And writes out a session to stdout that looks a lot like:
  username=me
  password=secret

When the provided host is wrong, no username or password will be provided.
"""
import re
import sys
import textwrap

import httplib2
from oauth2client import client

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as c_exc
from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import store as c_store


_KEYVAL_RE = re.compile(r'(.+)=(.+)')


@base.Hidden
class GitHelper(base.Command):
  """A git credential helper to provide access to Google git repositories."""

  @staticmethod
  def Args(parser):
    parser.add_argument('method',
                        help='The git credential helper method.')

  @c_exc.RaiseToolExceptionInsteadOf(c_store.Error, client.Error)
  def Run(self, args):
    """Run the helper command."""

    if args.method != 'get':
      return

    info = {}

    lines = sys.stdin.readlines()
    for line in lines:
      match = _KEYVAL_RE.match(line)
      if not match:
        continue
      key, val = match.groups()
      info[key] = val.strip()

    if info.get('protocol') != 'https':
      return

    credentialed_domains = ['code.google.com', 'source.developers.google.com']
    extra = properties.VALUES.core.credentialed_hosted_repo_domains.Get()
    if extra:
      credentialed_domains.extend(extra.split(','))
    if info.get('host') not in credentialed_domains:
      return

    account = properties.VALUES.core.account.Get()

    try:
      cred = c_store.Load(account)
    except c_store.Error as e:
      sys.stderr.write(textwrap.dedent("""\
          ERROR: {error}
          Run 'gcloud auth login' to log in.
          """.format(error=str(e))))
      return

    cred.refresh(httplib2.Http())

    sys.stdout.write(textwrap.dedent("""\
        username={username}
        password={password}
        """).format(username=account, password=cred.access_token))
