# Copyright 2013 Google Inc. All Rights Reserved.

"""The auth command gets tokens via oauth2."""

import webbrowser

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as c_exc
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import gce as c_gce
from googlecloudsdk.core.credentials import store as c_store


# A list of results for webbrowser.get().name that indicate we should not
# attempt to open a web browser for the user.
_WEBBROWSER_NAMES_BLACKLIST = [
    'www-browser',
]


class Login(base.Command):
  """Get credentials via Google's oauth2 web flow.

  Obtains access credentials for Google Cloud Platform resources, via a web
  flow, and makes them available for all the platform tools in the Cloud SDK. If
  a project is not provided, prompts for a default project.
  """

  @staticmethod
  def Args(parser):
    """Set args for gcloud auth."""

    parser.add_argument(
        '--no-launch-browser',
        action='store_false', default=True, dest='launch_browser',
        help=('Print a URL to be copied instead of launching a web browser.'))
    parser.add_argument(
        '--account', help='Override the account acquired from the web flow.')
    parser.add_argument(
        '--do-not-activate', action='store_true',
        help='Do not set the new credentials as active.')

  @c_exc.RaiseToolExceptionInsteadOf(c_store.Error)
  def Run(self, args):
    """Run the authentication command."""

    # Run the auth flow. Even if the user already is authenticated, the flow
    # will allow him or her to choose a different account.
    try:
      launch_browser = args.launch_browser and not c_gce.Metadata().connected

      # Sometimes it's not possible to launch the web browser. This often
      # happens when people ssh into other machines.
      if launch_browser:
        try:
          browser = webbrowser.get()
          if (hasattr(browser, 'name')
              and browser.name in _WEBBROWSER_NAMES_BLACKLIST):
            launch_browser = False
        except webbrowser.Error:
          launch_browser = False

      creds = c_store.AcquireFromWebFlow(
          launch_browser=launch_browser)
    except c_store.FlowError:
      log.error(
          ('There was a problem with the web flow. Try running with '
           '--no-launch-browser'))
      raise

    account = args.account
    if not account:
      account = creds.token_response['id_token']['email']

    c_store.Store(creds, account)

    if not args.do_not_activate:
      properties.PersistProperty(properties.VALUES.core.account, account)

    if args.project:
      properties.PersistProperty(properties.VALUES.core.project, args.project)

    return creds

  def Display(self, args, creds):
    account = creds.token_response['id_token']['email']
    log.out.write(
        '\nYou are logged in as {account}.\n'.format(account=account))
    if args.project:
      log.out.write("""
Project set to {project}.
You can change it at any time by running the following command.
 $ gcloud config set project NEW_PROJECT
""".format(project=args.project))

