# Copyright 2013 Google Inc. All Rights Reserved.

"""gcloud command line tool."""

import os
import signal
import sys

# If we're in a virtualenv, import site packages.
if os.environ.get('VIRTUAL_ENV'):
  # pylint:disable=unused-import
  # pylint:disable=g-import-not-at-top
  import site


def _SetPriorityCloudSDKPath():
  """Put google-cloud-sdk/lib at the beginning of sys.path.

  Modifying sys.path in this way allows us to always use our bundled versions
  of libraries, even when other versions have been installed. It also allows the
  user to install extra libraries that we cannot bundle (ie PyOpenSSL), and
  gcloud commands can use those libraries.
  """

  def _GetRootContainingGoogle():
    path = __file__
    while True:
      parent, here = os.path.split(path)
      if not here:
        break
      if here == 'googlecloudsdk':
        return parent
      path = parent

  module_root = _GetRootContainingGoogle()

  # check if we're already set
  if sys.path and module_root == sys.path[0]:
    return
  sys.path.insert(0, module_root)


def _DoStartupChecks():
  # pylint:disable=g-import-not-at-top
  from googlecloudsdk.core.util import platforms
  if not platforms.PythonVersion().IsSupported():
    sys.exit(1)
  if not platforms.Platform.Current().IsSupported():
    sys.exit(1)

_SetPriorityCloudSDKPath()
_DoStartupChecks()

# pylint:disable=g-import-not-at-top, We want the _SetPriorityCloudSDKPath()
# function to be called before we try to import any CloudSDK modules.
from googlecloudsdk.core import cli
from googlecloudsdk.core import log
from googlecloudsdk.core import metrics
from googlecloudsdk.core import properties
from googlecloudsdk.core.updater import local_state
from googlecloudsdk.core.updater import update_manager


# Don't know stack traces when people kill a command.
def CTRLCHandler(unused_signal, unused_frame):
  log.err.Print('\n\nCommand killed by Ctrl+C\n')
  sys.exit(1)
signal.signal(signal.SIGINT, CTRLCHandler)




def UpdateCheck():
  try:
    update_manager.UpdateManager().PerformUpdateCheck()
  # pylint:disable=broad-except, We never want this to escape, ever. Only
  # messages printed should reach the user.
  except Exception:
    pass


def VersionFunc():
  _loader.Execute(['version'])

sdk_root = local_state.InstallationState.FindSDKInstallRoot(__file__)
if sdk_root:
  help_dir = os.path.join(sdk_root, 'help')
else:
  help_dir = None
_loader = cli.CLI(
    name='gcloud',
    command_root_directory=os.path.join(
        cli.GoogleCloudSDKPackageRoot(),
        'gcloud',
        'sdktools',
        'root'),
    allow_non_existing_modules=True,
    module_directories={
        'app': os.path.join(
            cli.GoogleCloudSDKPackageRoot(),
            'appengine',
            'commands'),
        'auth': os.path.join(
            cli.GoogleCloudSDKPackageRoot(),
            'gcloud',
            'sdktools',
            'auth'),
        'components': os.path.join(
            cli.GoogleCloudSDKPackageRoot(),
            'gcloud',
            'sdktools',
            'components'),
        'compute': os.path.join(
            cli.GoogleCloudSDKPackageRoot(),
            'compute',
            'subcommands'),
        'config': os.path.join(
            cli.GoogleCloudSDKPackageRoot(),
            'gcloud',
            'sdktools',
            'config'),
        'datastore': os.path.join(
            cli.GoogleCloudSDKPackageRoot(),
            'appengine',
            'datastore_commands'),
        'dns': os.path.join(
            cli.GoogleCloudSDKPackageRoot(),
            'dns',
            'dnstools'),
        'endpoints': os.path.join(
            cli.GoogleCloudSDKPackageRoot(),
            'endpoints',
            'commands'),
        'preview': os.path.join(
            cli.GoogleCloudSDKPackageRoot(),
            'preview',
            'commands'),
        'sql': os.path.join(
            cli.GoogleCloudSDKPackageRoot(),
            'sql',
            'tools'),
    },
    version_func=VersionFunc,
    help_dir=help_dir,
)

# Check for updates on shutdown but not for any of the updater commands.
_loader.RegisterPostRunHook(UpdateCheck,
                            exclude_commands=r'gcloud\.components\..*')
gcloud = _loader.EntryPoint()


def main():
  # TODO(user): Put a real version number here
  metrics.Executions(
      'gcloud',
      local_state.InstallationState.VersionForInstalledComponent('core'))
  _loader.Execute()

if __name__ == '__main__':
  try:
    main()
  except KeyboardInterrupt:
    CTRLCHandler(None, None)
