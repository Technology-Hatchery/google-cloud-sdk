# Copyright 2013 Google Inc. All Rights Reserved.

"""Config for Google Cloud Platform CLIs."""

import json
import os


from googlecloudsdk.core.util import files as file_utils
from googlecloudsdk.core.util import platforms


class Error(Exception):
  """Exceptions for the cli module."""


class GooglePackageRootNotFoundException(Error):
  """An exception to be raised when the google root is unable to be found.

  This exception should never be raised, and indicates a problem with the
  environment.
  """


def GoogleCloudSDKPackageRoot():

  # pylint:disable=unreachable, would be nicer to have MOE insert this block.
  resource_dir = file_utils.FindDirectoryContaining(
      os.path.dirname(__file__), 'googlecloudsdk')
  if not resource_dir:
    raise GooglePackageRootNotFoundException()
  return os.path.join(resource_dir, 'googlecloudsdk')


# Environment variable for the directory containing Cloud SDK configuration.
CLOUDSDK_CONFIG = 'CLOUDSDK_CONFIG'

# Common shell script preamble for ${CLOUDSDK_SH_PREAMBLE} templates.
CLOUDSDK_SH_PREAMBLE = """\
# <cloud-sdk-preamble>
#
#  CLOUDSDK_ROOT_DIR      (a)  installation root dir
#  CLOUDSDK_PYTHON        (u)  python interpreter path
#  CLOUDSDK_PYTHON_ARGS   (u)  python interpreter arguments
#
# (a) always defined by the preamble
# (u) user definition overrides preamble

# Determines the real cloud sdk root dir given the script path.
# Would be easier with a portable "readlink -f".
_cloudsdk_root_dir() {
  case $1 in
  /*)   _cloudsdk_path=$1
        ;;
  */*)  _cloudsdk_path=$PWD/$1
        ;;
  *)    _cloudsdk_path=$(which "$1")
        case $_cloudsdk_path in
        /*) ;;
        *)  _cloudsdk_path=$PWD/$_cloudsdk_path ;;
        esac
        ;;
  esac
  _cloudsdk_dir=0
  while :
  do
    while _cloudsdk_link=$(readlink "$_cloudsdk_path")
    do
      case $_cloudsdk_link in
      /*) _cloudsdk_path=$_cloudsdk_link ;;
      *)  _cloudsdk_path=$(dirname "$_cloudsdk_path")/$_cloudsdk_link ;;
      esac
    done
    case $_cloudsdk_dir in
    1)  break ;;
    esac
    _cloudsdk_dir=1
    _cloudsdk_path=$(dirname "$_cloudsdk_path")
  done
  while :
  do  case $_cloudsdk_path in
      */.)    _cloudsdk_path=$(dirname "$_cloudsdk_path")
              ;;
      */bin)  dirname "$_cloudsdk_path"
              break
              ;;
      *)      echo "$_cloudsdk_path"
              break
              ;;
      esac
  done
}
CLOUDSDK_ROOT_DIR=$(_cloudsdk_root_dir "$0")

[ -z "$CLOUDSDK_PYTHON" ] &&
  CLOUDSDK_PYTHON=python

[ -n "$_always_use_site_packages" ] && export CLOUDSDK_PYTHON_SITEPACKAGES=1

[ -z "$CLOUDSDK_PYTHON_ARGS" -a -z "$CLOUDSDK_PYTHON_SITEPACKAGES" ] &&
  CLOUDSDK_PYTHON_ARGS=-S

export CLOUDSDK_ROOT_DIR CLOUDSDK_PYTHON_ARGS

# </cloud-sdk-preamble>
"""


class InstallationConfig(object):
  """Loads configuration constants from the core config file.

  Attributes:
    version: str, The version of the core component.
    user_agent: str, The base string of the user agent to use when making API
      calls.
    documentation_url: str, The URL where we can redirect people when they need
      more information.
    snapshot_url: str, The url for the component manager to look at for
      updates.
    disable_updater: bool, True to disable the component manager for this
      installation.  We do this for distributions through another type of
      package manager like apt-get.
    disable_usage_reporting: bool, True to disable the sending of usage data by
      default.
    snapshot_schema_version: int, The version of the snapshot schema this code
      understands.
    release_channel: str, The release channel for this Cloud SDK distribution.
      The default is 'stable'.
    config_suffix: str, A string to add to the end of the configuration
      directory name so that different release channels can have separate
      config.
  """

  @staticmethod
  def Load():
    """Initializes the object with values from the config file.

    Returns:
      InstallationSpecificData: The loaded data.
    """
    config_file = os.path.join(GoogleCloudSDKPackageRoot(),
                               'core', 'config.json')
    with open(config_file) as f:
      data = json.load(f)
    return InstallationConfig(**data)

  def __init__(self, version, user_agent, documentation_url, snapshot_url,
               disable_updater, disable_usage_reporting,
               snapshot_schema_version, release_channel, config_suffix):
    # JSON returns all unicode.  We know these are regular strings and using
    # unicode in environment variables on Windows doesn't work.
    self.version = str(version)
    self.user_agent = str(user_agent)
    self.documentation_url = str(documentation_url)
    self.snapshot_url = str(snapshot_url)
    self.disable_updater = disable_updater
    self.disable_usage_reporting = disable_usage_reporting
    # This one is an int, no need to convert
    self.snapshot_schema_version = snapshot_schema_version
    self.release_channel = str(release_channel)
    self.config_suffix = str(config_suffix)

  def IsAlternateReleaseChannel(self):
    """Determines if this distribution is using an alternate release channel.

    Returns:
      True if this distribution is not the 'stable' release channel, False
      otherwise.
    """
    return self.release_channel != 'stable'


INSTALLATION_CONFIG = InstallationConfig.Load()

# TODO(user): Have this version get set automatically somehow. Replacer?
CLOUD_SDK_VERSION = INSTALLATION_CONFIG.version
# TODO(user): Distribute a clientsecrets.json to avoid putting this in code.
CLOUDSDK_CLIENT_ID = '32555940559.apps.googleusercontent.com'
CLOUDSDK_CLIENT_NOTSOSECRET = 'ZmssLNjJy2998hD4CTg2ejr2'

CLOUDSDK_USER_AGENT = INSTALLATION_CONFIG.user_agent

# TODO(user): Consider a way to allow users to choose a smaller scope set,
# knowing that things might fail if they try to use a tool with scopes that have
# not been granted.
CLOUDSDK_SCOPES = [
    'https://www.googleapis.com/auth/appengine.admin',
    'https://www.googleapis.com/auth/bigquery',
    'https://www.googleapis.com/auth/compute',
    'https://www.googleapis.com/auth/devstorage.full_control',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/ndev.cloudman',
    'https://www.googleapis.com/auth/cloud-platform',
    'https://www.googleapis.com/auth/sqlservice.admin',
    'https://www.googleapis.com/auth/prediction',
    'https://www.googleapis.com/auth/projecthosting',
]




def _CheckForExtraScopes():
  extra_scopes = os.environ.get('CLOUDSDK_EXTRA_SCOPES')
  if not extra_scopes:
    return
  CLOUDSDK_SCOPES.extend(extra_scopes.split())

_CheckForExtraScopes()


class Paths(object):
  """Class to encapsulate the various directory paths of the Cloud SDK.

  Attributes:
    global_config_dir: str, The path to the user's global config area.
    workspace_dir: str, The path of the current workspace or None if not in a
      workspace.
    workspace_config_dir: str, The path to the config directory under the
      current workspace, or None if not in a workspace.
  """
  # Name of the directory that roots a cloud SDK workspace.
  _CLOUDSDK_WORKSPACE_CONFIG_WORD = ('gcloud' +
                                     INSTALLATION_CONFIG.config_suffix)
  CLOUDSDK_WORKSPACE_CONFIG_DIR_NAME = '.%s' % _CLOUDSDK_WORKSPACE_CONFIG_WORD

  def __init__(self):
    if platforms.OperatingSystem.Current() == platforms.OperatingSystem.WINDOWS:
      try:
        default_config_path = os.path.join(
            os.environ['APPDATA'], Paths._CLOUDSDK_WORKSPACE_CONFIG_WORD)
      except KeyError:
        # This should never happen unless someone is really messing with things.
        drive = os.environ.get('SystemDrive', 'C:')
        default_config_path = os.path.join(
            drive, '\\', Paths._CLOUDSDK_WORKSPACE_CONFIG_WORD)
    else:
      default_config_path = os.path.join(
          os.path.expanduser('~'), '.config',
          Paths._CLOUDSDK_WORKSPACE_CONFIG_WORD)
    self.global_config_dir = os.getenv(CLOUDSDK_CONFIG, default_config_path)
    self.workspace_dir = file_utils.FindDirectoryContaining(
        os.getcwd(), Paths.CLOUDSDK_WORKSPACE_CONFIG_DIR_NAME)
    self.workspace_config_dir = None
    if self.workspace_dir:
      self.workspace_config_dir = os.path.join(
          self.workspace_dir, Paths.CLOUDSDK_WORKSPACE_CONFIG_DIR_NAME)

  @property
  def config_dir(self):
    """The directory to use for configuration.

    If in a workspace, that config directory will be used, otherwise the global
    one will be used.

    Returns:
      str, The path to the config directory.
    """
    if self.workspace_config_dir:
      return self.workspace_config_dir
    return self.global_config_dir

  @property
  def credentials_path(self):
    """Gets the path to the file to store credentials in.

    Credentials are always stored in global config, never the local workspace.
    This is due to the fact that local workspaces are likely to be stored whole
    in source control, and we don't want to accidentally publish credential
    information.  We also want user credentials to be shared across workspaces
    if they are for the same user.

    Returns:
      str, The path to the credential file.
    """
    return os.path.join(self.global_config_dir, 'credentials')

  @property
  def config_json_path(self):
    """Gets the path to the file to use for persistent json storage in calliope.

    Returns:
      str, The path to the file to use for storage.
    """
    return os.path.join(self.config_dir, 'config.json')

  @property
  def logs_dir(self):
    """Gets the path to the directory to put logs in for calliope commands.

    Returns:
      str, The path to the directory to put logs in.
    """
    return os.path.join(self.config_dir, 'logs')

  @property
  def analytics_cid_path(self):
    """Gets the path to the file to store the client id for analytics.

    This is always stored in the global location because it is per install.

    Returns:
      str, The path the file.
    """
    return os.path.join(self.global_config_dir, '.metricsUUID')

  @property
  def global_properties_path(self):
    """Gets the path to the properties file in the global config dir.

    Returns:
      str, The path to the file.
    """
    return os.path.join(self.global_config_dir, 'properties')

  @property
  def workspace_properties_path(self):
    """Gets the path to the properties file in your local workspace.

    Returns:
      str, The path to the file, or None if there is no local workspace.
    """
    if not self.workspace_config_dir:
      return None
    return os.path.join(self.workspace_config_dir, 'properties')

  def LegacyCredentialsDir(self, account):
    """Gets the path to store legacy multistore credentials in.

    Args:
      account: str, Email account tied to the authorizing credentials.

    Returns:
      str, The path to the multistore credentials file.
    """
    if not account:
      account = 'default'
    return os.path.join(self.global_config_dir, 'legacy_credentials', account)

  def LegacyCredentialsMultistorePath(self, account):
    """Gets the path to store legacy multistore credentials in.

    Args:
      account: str, Email account tied to the authorizing credentials.

    Returns:
      str, The path to the multistore credentials file.
    """
    return os.path.join(self.LegacyCredentialsDir(account), 'multistore.json')

  def LegacyCredentialsJSONPath(self, account):
    """Gets the path to store legacy JSON credentials in.

    Args:
      account: str, Email account tied to the authorizing credentials.

    Returns:
      str, The path to the JSON credentials file.
    """
    return os.path.join(self.LegacyCredentialsDir(account), 'singlestore.json')

  def LegacyCredentialsGAEJavaPath(self, account):
    """Gets the path to store legacy GAE for Java credentials in.

    Args:
      account: str, Email account tied to the authorizing credentials.

    Returns:
      str, The path to the  GAE for Java credentials file.
    """
    return os.path.join(self.LegacyCredentialsDir(account), 'gaejava.txt')

  def LegacyCredentialsGSUtilPath(self, account):
    """Gets the path to store legacy gsutil credentials in.

    Args:
      account: str, Email account tied to the authorizing credentials.

    Returns:
      str, The path to the gsutil credentials file.
    """
    return os.path.join(self.LegacyCredentialsDir(account), '.boto')

  def LegacyCredentialsKeyPath(self, account):
    """Gets the path to store legacy key file in.

    Args:
      account: str, Email account tied to the authorizing credentials.

    Returns:
      str, The path to the key file.
    """
    return os.path.join(self.LegacyCredentialsDir(account), 'private_key.p12')

  def GCECachePath(self):
    """Get the path to cache whether or not we're on a GCE machine.

    Returns:
      str, The path to the GCE cache.
    """
    return os.path.join(self.global_config_dir, 'gce')
