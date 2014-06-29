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
from googlecloudsdk.core import resources
from googlecloudsdk.core.updater import local_state
from googlecloudsdk.core.updater import update_manager


def RegisterAPIs():
  """Register all the bundled Cloud APIs."""
  # pylint:disable=g-import-not-at-top
  from googlecloudapis.compute import v1 as compute_v1
  from googlecloudapis.dns import v1beta1 as dns_v1beta1
  from googlecloudapis.manager import v1beta2 as manager_v1beta2
  from googlecloudapis.replicapool import v1beta1 as replicapool_v1beta1
  from googlecloudapis.resourceviews import v1beta1 as resourceviews_v1beta1
  from googlecloudapis.sqladmin import v1beta3 as sqladmin_v1beta3
  resources.RegisterAPI(compute_v1.ComputeV1(get_credentials=False))
  resources.RegisterAPI(dns_v1beta1.DnsV1beta1(get_credentials=False))
  resources.RegisterAPI(manager_v1beta2.ManagerV1beta2(get_credentials=False))
  resources.RegisterAPI(
      replicapool_v1beta1.ReplicapoolV1beta1(get_credentials=False))
  resources.RegisterAPI(
      resourceviews_v1beta1.ResourceviewsV1beta1(get_credentials=False))
  resources.RegisterAPI(sqladmin_v1beta3.SqladminV1beta3(get_credentials=False))

RegisterAPIs()




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
  _cli.Execute(['version'])


def CreateCLI():
  """Generates the gcloud CLI."""
  sdk_root = local_state.InstallationState.FindSDKInstallRoot(__file__)
  if sdk_root:
    help_dir = os.path.join(sdk_root, 'help')
  else:
    help_dir = None
  loader = cli.CLILoader(
      name='gcloud',
      command_root_directory=os.path.join(
          cli.GoogleCloudSDKPackageRoot(),
          'gcloud',
          'sdktools',
          'root'),
      allow_non_existing_modules=True,
      version_func=VersionFunc,
      help_dir=help_dir)
  pkg_root = cli.GoogleCloudSDKPackageRoot()
  loader.AddModule('auth', os.path.join(pkg_root, 'gcloud', 'sdktools', 'auth'))
  loader.AddModule('bq', os.path.join(pkg_root, 'bq', 'commands'))
  loader.AddModule('components',
                   os.path.join(pkg_root, 'gcloud', 'sdktools', 'components'))
  loader.AddModule('compute', os.path.join(pkg_root, 'compute', 'subcommands'))
  loader.AddModule('config',
                   os.path.join(pkg_root, 'gcloud', 'sdktools', 'config'))
  loader.AddModule('dns', os.path.join(pkg_root, 'dns', 'dnstools'))
  loader.AddModule('endpoints', os.path.join(pkg_root, 'endpoints', 'commands'))
  loader.AddModule('preview', os.path.join(pkg_root, 'preview', 'commands'))
  # Put app and datastore under preview for now.
  loader.AddModule('preview.app',
                   os.path.join(pkg_root, 'appengine', 'app_commands'))
  loader.AddModule('preview.datastore',
                   os.path.join(pkg_root, 'appengine', 'datastore_commands'))
  loader.AddModule('sql', os.path.join(pkg_root, 'sql', 'tools'))

  # Check for updates on shutdown but not for any of the updater commands.
  loader.RegisterPostRunHook(UpdateCheck,
                             exclude_commands=r'gcloud\.components\..*')
  return loader.Generate()

_cli = CreateCLI()
gcloud = _cli.EntryPoint()


def main():
  # TODO(user): Put a real version number here
  metrics.Executions(
      'gcloud',
      local_state.InstallationState.VersionForInstalledComponent('core'))
  _cli.Execute()

if __name__ == '__main__':
  try:
    main()
  except KeyboardInterrupt:
    CTRLCHandler(None, None)
