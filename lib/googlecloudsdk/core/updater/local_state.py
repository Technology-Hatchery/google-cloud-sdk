# Copyright 2013 Google Inc. All Rights Reserved.

"""Manages the state of what is installed in the cloud SDK.

This tracks the installed modules along with the files they created.  It also
provides functionality like extracting tar files into the installation and
tracking when we check for updates.
"""

import errno
import json
import logging
import os
import shutil
import sys
import time

from googlecloudsdk.core.updater import installers
from googlecloudsdk.core.updater import snapshots
from googlecloudsdk.core.util import files as file_utils


class Error(Exception):
  """Base exception for the local_state module."""
  pass


class InvalidSDKRootError(Error):
  """Error for when the root of the Cloud SDK is invalid or cannot be found."""
  pass


class URLFetchError(Error):
  """Exception for problems fetching via HTTP."""
  pass


class InvalidDownloadError(Error):
  """Exception for when the SDK that was download was invalid."""
  pass


class PermissionsError(Error):
  """Error for when a file operation cannot complete due to permissions."""

  def __init__(self, path):
    """Initialize a PermissionsError.

    Args:
      path: str, The absolute path to a file or directory that needs to be
          operated on, but can't because of insufficient permssions.
    """
    super(PermissionsError, self).__init__(
        'Insufficient permission to access: {path}'.format(path=path))


def _RaisesPermissionsError(func):
  """Use this decorator for functions that deal with files.

  If an exception indicating file permissions is raised, this decorator will
  raise a PermissionsError instead, so that the caller only has to watch for
  one type of exception.

  Args:
    func: The function to decorate.

  Returns:
    A decorator.
  """

  def _TryFunc(*args, **kwargs):
    try:
      return func(*args, **kwargs)
    except (OSError, IOError) as e:
      if e.errno == errno.EACCES:
        raise PermissionsError(os.path.abspath(e.filename))
      raise
    except shutil.Error as e:
      args = e.args[0][0]
      # unfortunately shutil.Error *only* has formatted strings to inspect.
      # Looking for this substring is looking for errno.EACCES, which has
      # a numeric value of 13.
      if args[2].startswith('[Errno 13]'):
        raise PermissionsError(os.path.abspath(args[0]))
      raise
  return _TryFunc


class InstallationState(object):
  """The main class for checking / updating local installation state."""

  STATE_DIR_NAME = '.install'
  BACKUP_DIR_NAME = '.backup'
  TRASH_DIR_NAME = '.trash'
  STAGING_ROOT_SUFFIX = '.staging'
  COMPONENT_SNAPSHOT_FILE_SUFFIX = '.snapshot.json'

  @staticmethod
  def FindSDKInstallRoot(starting_dir):
    """Searches for the Cloud SDK installation directory.

    This will recursively search upwards from the given directory until it finds
    a directory with a '.install' in it.

    Args:
      starting_dir: str, The path to start looking in.

    Returns:
      str, The path to the root of the Cloud SDK or None if it could not be
      found.
    """
    return file_utils.FindDirectoryContaining(starting_dir,
                                              InstallationState.STATE_DIR_NAME)

  @staticmethod
  def ForCurrent():
    """Gets the installation state for the SDK that this code is running in.

    Returns:
      InstallationState, The state for this area.

    Raises:
      InvalidSDKRootError: If this code is not running under a valid SDK.
    """
    sdk_root = InstallationState.FindSDKInstallRoot(os.path.dirname(__file__))
    if not sdk_root:
      raise InvalidSDKRootError(
          'Could not locate the install root of the Cloud SDK.')
    return InstallationState(os.path.realpath(sdk_root))

  @staticmethod
  def VersionForInstalledComponent(component_id):
    """Gets the version string for the given installed component.

    This function is to be used to get component versions for metrics reporting.
    If it fails in any way or if the component_id is unknown, it will return
    None.  This prevents errors from surfacing when the version is needed
    strictly for reporting purposes.

    Args:
      component_id: str, The component id of the component you want the version
        for.

    Returns:
      str, The installed version of the component, or None if it is not
        installed or if an error occurs.
    """
    try:
      state = InstallationState.ForCurrent()
      # pylint: disable=protected-access, This is the same class.
      return InstallationManifest(
          state._state_directory, component_id).VersionString()
    # pylint: disable=bare-except, We never want to fail because of metrics.
    except:
      logging.debug('Failed to get installed version for component [%s]: [%s]',
                    component_id, sys.exc_info())
    return None

  @_RaisesPermissionsError
  def __init__(self, sdk_root):
    """Initializes the installation state for the given sdk install.

    Args:
      sdk_root: str, The file path of the root of the SDK installation.

    Raises:
      ValueError: If the given SDK root does not exist.
    """
    if not os.path.isdir(sdk_root):
      raise ValueError('The given Cloud SDK root does not exist: [{}]'
                       .format(sdk_root))

    self.__sdk_root = sdk_root
    self._state_directory = os.path.join(sdk_root,
                                         InstallationState.STATE_DIR_NAME)
    self.__backup_directory = os.path.join(self._state_directory,
                                           InstallationState.BACKUP_DIR_NAME)
    self.__trash_directory = os.path.join(self._state_directory,
                                          InstallationState.TRASH_DIR_NAME)

    self.__sdk_staging_root = (os.path.normpath(self.__sdk_root) +
                               InstallationState.STAGING_ROOT_SUFFIX)

    for d in [self._state_directory]:
      if not os.path.isdir(d):
        file_utils.MakeDir(d)

  @property
  def sdk_root(self):
    """Gets the root of the SDK that this state corresponds to.

    Returns:
      str, the path to the root directory.
    """
    return self.__sdk_root

  def _FilesForSuffix(self, suffix):
    """Returns the files in the state directory that have the given suffix.

    Args:
      suffix: str, The file suffix to match on.

    Returns:
      list of str, The file names that match.
    """
    files = os.listdir(self._state_directory)
    matching = [f for f in files
                if os.path.isfile(os.path.join(self._state_directory, f))
                and f.endswith(suffix)]
    return matching

  @_RaisesPermissionsError
  def InstalledComponents(self):
    """Gets all the components that are currently installed.

    Returns:
      A dictionary of component id string to InstallationManifest.
    """
    snapshot_files = self._FilesForSuffix(
        InstallationState.COMPONENT_SNAPSHOT_FILE_SUFFIX)
    manifests = {}
    for f in snapshot_files:
      component_id = f[:-len(InstallationState.COMPONENT_SNAPSHOT_FILE_SUFFIX)]
      manifests[component_id] = InstallationManifest(self._state_directory,
                                                     component_id)
    return manifests

  @_RaisesPermissionsError
  def Snapshot(self):
    """Generates a ComponentSnapshot from the currently installed components."""
    return snapshots.ComponentSnapshot.FromInstallState(self)

  def LastUpdateCheck(self):
    """Gets a LastUpdateCheck object to check update status."""
    return LastUpdateCheck(self)

  def DiffCurrentState(self, latest_snapshot, platform_filter=None):
    """Generates a ComponentSnapshotDiff from current state and the given state.

    Args:
      latest_snapshot:  snapshots.ComponentSnapshot, The current state of the
        world to diff against.
      platform_filter: platforms.Platform, A platform that components must
        match in order to be considered for any operations.

    Returns:
      A ComponentSnapshotDiff.
    """
    return self.Snapshot().CreateDiff(latest_snapshot,
                                      platform_filter=platform_filter)

  @_RaisesPermissionsError
  def CloneToStaging(self):
    """Clones this state to the temporary staging area.

    This is used for making temporary copies of the entire Cloud SDK
    installation when doing updates.  The entire installation is cloned, but
    doing so removes any backups and trash from this state before doing the
    copy.

    Returns:
      An InstallationState object for the cloned install.
    """
    if os.path.exists(self.__sdk_staging_root):
      file_utils.RmTree(self.__sdk_staging_root)
    self.ClearBackup()
    self.ClearTrash()
    shutil.copytree(self.__sdk_root, self.__sdk_staging_root, symlinks=True)
    return InstallationState(self.__sdk_staging_root)

  @_RaisesPermissionsError
  def CreateStagingFromDownload(self, url):
    """Creates a new staging area from a fresh download of the Cloud SDK.

    Args:
      url: str, The url to download the new SDK from.

    Returns:
      An InstallationState object for the new install.

    Raises:
      URLFetchError: If the new SDK could not be downloaded.
      InvalidDownloadError: If the new SDK was malformed.
    """
    if os.path.exists(self.__sdk_staging_root):
      file_utils.RmTree(self.__sdk_staging_root)

    with file_utils.TemporaryDirectory() as t:
      download_dir = os.path.join(t, '.download')
      extract_dir = os.path.join(t, '.extract')
      try:
        installers.ComponentInstaller.DownloadAndExtractTar(
            url, download_dir, extract_dir)
      except installers.URLFetchError as e:
        raise URLFetchError(e)
      files = os.listdir(extract_dir)
      if len(files) != 1:
        raise InvalidDownloadError('The downloaded SDK was invalid')
      sdk_root = os.path.join(extract_dir, files[0])
      file_utils.MoveDir(sdk_root, self.__sdk_staging_root)
    return InstallationState(self.__sdk_staging_root)

  @_RaisesPermissionsError
  def ReplaceWith(self, other_install_state):
    """Replaces this installation with the given other installation.

    This moves the current installation to the backup directory of the other
    installation.  Then, it moves the entire second installation to replace
    this one on the file system.  The result is that the other installation
    completely replaces the current one, but the current one is snapshotted and
    stored as a backup under the new one (and can be restored later).

    Args:
      other_install_state: InstallationState, The other state with which to
        replace this one.
    """
    self.ClearBackup()
    self.ClearTrash()
    other_install_state.ClearBackup()
    # pylint: disable=protected-access, This is an instance of InstallationState
    file_utils.MoveDir(self.__sdk_root, other_install_state.__backup_directory)
    file_utils.MoveDir(other_install_state.__sdk_root, self.__sdk_root)

  @_RaisesPermissionsError
  def RestoreBackup(self):
    """Restore the backup from this install state if it exists.

    If this installation has a backup stored in it (created by and update that
    used ReplaceWith(), above), it replaces this installation with the backup,
    using a temporary staging area.  This installation is moved to the trash
    directory under the installation that exists after this is done.  The trash
    directory can be removed at any point in the future.  We just don't want to
    delete code that is running since some platforms have a problem with that.

    Returns:
      bool, True if there was a backup to restore, False otherwise.
    """
    if not self.HasBackup():
      return False

    if os.path.exists(self.__sdk_staging_root):
      file_utils.RmTree(self.__sdk_staging_root)

    file_utils.MoveDir(self.__backup_directory, self.__sdk_staging_root)
    staging_state = InstallationState(self.__sdk_staging_root)
    staging_state.ClearTrash()
    # pylint: disable=protected-access, This is an instance of InstallationState
    file_utils.MoveDir(self.__sdk_root, staging_state.__trash_directory)
    file_utils.MoveDir(staging_state.__sdk_root, self.__sdk_root)
    return True

  def HasBackup(self):
    """Determines if this install has a valid backup that can be restored.

    Returns:
      bool, True if there is a backup, False otherwise.
    """
    return os.path.isdir(self.__backup_directory)

  def BackupDirectory(self):
    """Gets the backup directory of this installation if it exists.

    Returns:
      str, The path to the backup directory or None if it does not exist.
    """
    if self.HasBackup():
      return self.__backup_directory
    return None

  @_RaisesPermissionsError
  def ClearBackup(self):
    """Deletes the current backup if it exists."""
    if os.path.isdir(self.__backup_directory):
      file_utils.RmTree(self.__backup_directory)

  @_RaisesPermissionsError
  def ClearTrash(self):
    """Deletes the current trash directory if it exists."""
    if os.path.isdir(self.__trash_directory):
      file_utils.RmTree(self.__trash_directory)

  def _GetInstaller(self, snapshot):
    """Gets a component installer based on the given snapshot.

    Args:
      snapshot: snapshots.ComponentSnapshot, The snapshot that describes the
        component to install.

    Returns:
      The installers.ComponentInstaller.
    """
    return installers.ComponentInstaller(self.__sdk_root,
                                         self._state_directory,
                                         snapshot)

  @_RaisesPermissionsError
  def Install(self, snapshot, component_id):
    """Installs the given component based on the given snapshot.

    Args:
      snapshot: snapshots.ComponentSnapshot, The snapshot that describes the
        component to install.
      component_id: str, The component to install from the given snapshot.

    Raises:
      installers.URLFetchError: If the component associated with the provided
        component ID has a URL that is not fetched correctly.
    """
    files = self._GetInstaller(snapshot).Install(component_id)
    manifest = InstallationManifest(self._state_directory, component_id)
    manifest.MarkInstalled(snapshot, files)

  @_RaisesPermissionsError
  def Uninstall(self, component_id):
    """Uninstalls the given component.

    Deletes all the files for this component and marks it as no longer being
    installed.

    Args:
      component_id: str, The id of the component to uninstall.
    """
    manifest = InstallationManifest(self._state_directory, component_id)
    files = manifest.InstalledFiles()
    root = self.__sdk_root

    dirs_to_remove = set()
    for f in files:
      path = os.path.join(root, f)
      if os.path.isfile(path) or os.path.islink(path):
        os.remove(path)
        # Clean up the pyc files that correspond to any py files being removed.
        if f.endswith('.py'):
          pyc_path = path + 'c'
          if os.path.isfile(pyc_path):
            os.remove(pyc_path)
        dir_path = os.path.dirname(path)
        if dir_path:
          dirs_to_remove.add(os.path.normpath(dir_path))
      elif os.path.isdir(path):
        dirs_to_remove.add(os.path.normpath(path))

    # Remove dirs from the bottom up.  Subdirs will always have a longer path
    # than it's parent.
    for d in sorted(dirs_to_remove, key=len, reverse=True):
      if os.path.isdir(d) and not os.path.islink(d) and not os.listdir(d):
        os.rmdir(d)

    manifest.MarkUninstalled()


class InstallationManifest(object):
  """Class to encapsulate the data stored in installation manifest files."""

  MANIFEST_SUFFIX = '.manifest'

  def __init__(self, state_dir, component_id):
    """Creates a new InstallationManifest.

    Args:
      state_dir: str, The directory path where install state is stored.
      component_id: str, The component id that you want to get the manifest for.
    """
    self.state_dir = state_dir
    self.id = component_id
    self.snapshot_file = os.path.join(
        self.state_dir,
        component_id + InstallationState.COMPONENT_SNAPSHOT_FILE_SUFFIX)
    self.manifest_file = os.path.join(
        self.state_dir,
        component_id + InstallationManifest.MANIFEST_SUFFIX)

  def MarkInstalled(self, snapshot, files):
    """Marks this component as installed with the given snapshot and files.

    This saves the ComponentSnapshot and writes the installed files to a
    manifest so they can be removed later.

    Args:
      snapshot: snapshots.ComponentSnapshot, The snapshot that was the source
        of the install.
      files: list of str, The files that were created by the installation.
    """
    with open(self.manifest_file, 'w') as fp:
      for f in files:
        fp.write(f + '\n')
    snapshot.WriteToFile(self.snapshot_file)

  def MarkUninstalled(self):
    """Marks this component as no longer being installed.

    This does not actually uninstall the component, but rather just removes the
    snapshot and manifest.
    """
    for f in [self.manifest_file, self.snapshot_file]:
      if os.path.isfile(f):
        os.remove(f)

  def ComponentSnapshot(self):
    """Loads the local ComponentSnapshot for this component.

    Returns:
      The snapshots.ComponentSnapshot for this component.
    """
    return snapshots.ComponentSnapshot.FromFile(self.snapshot_file)

  def ComponentDefinition(self):
    """Loads the ComponentSnapshot and get the schemas.Component this component.

    Returns:
      The schemas.Component for this component.
    """
    return self.ComponentSnapshot().ComponentFromId(self.id)

  def VersionString(self):
    """Gets the version string of this component as it was installed.

    Returns:
      str, The installed version of this component.
    """
    return self.ComponentDefinition().version.version_string

  def InstalledFiles(self):
    """Gets the list of files created by installing this component.

    Returns:
      list of str, The files installed by this component.
    """
    with open(self.manifest_file) as f:
      files = [line.rstrip() for line in f]
    return files


class LastUpdateCheck(object):
  """A class to encapsulate information on when we last checked for updates."""

  LAST_UPDATE_CHECK_FILE = 'last_update_check.json'
  DATE = 'date'
  REVISION = 'revision'
  UPDATES_AVAILABLE = 'updates_available'

  def __init__(self, install_state):
    self.__install_state = install_state
    # pylint: disable=protected-access, These classes work together
    self.__last_update_check_file = os.path.join(
        install_state._state_directory, LastUpdateCheck.LAST_UPDATE_CHECK_FILE)
    (self.__last_update_check_date,
     self.__last_update_check_revision,
     self.__updates_available) = self._LoadData()

  def _LoadData(self):
    if not os.path.isfile(self.__last_update_check_file):
      return (0, 0, False)
    with open(self.__last_update_check_file) as fp:
      data = json.loads(fp.read())
      return (data[LastUpdateCheck.DATE],
              data[LastUpdateCheck.REVISION],
              data[LastUpdateCheck.UPDATES_AVAILABLE])

  def _SaveData(self):
    data = {LastUpdateCheck.DATE: self.__last_update_check_date,
            LastUpdateCheck.REVISION: self.__last_update_check_revision,
            LastUpdateCheck.UPDATES_AVAILABLE: self.__updates_available}
    with open(self.__last_update_check_file, 'w') as fp:
      fp.write(json.dumps(data))

  def UpdatesAvailable(self):
    """Returns whether we already know about updates that are available.

    Returns:
      bool, True if we know about updates, False otherwise.
    """
    return self.__updates_available

  def LastUpdateCheckRevision(self):
    """Gets the revision of the snapshot from the last update check.

    Returns:
      int, The revision of the last checked snapshot.
    """
    return self.__last_update_check_revision

  def LastUpdateCheckDate(self):
    """Gets the time of the last update check as seconds since the epoch.

    Returns:
      int, The time of the last update check.
    """
    return self.__last_update_check_date

  def SecondsSinceLastUpdateCheck(self):
    """Gets the number of seconds since we last did an update check.

    Returns:
      int, The amount of time in seconds.
    """
    return time.time() - self.__last_update_check_date

  @_RaisesPermissionsError
  def SetFromSnapshot(self, snapshot, force=False):
    """Sets that we just did an update check and found the given snapshot.

    If the given snapshot is different that the last one we saw, this will also
    diff the new snapshot with the current install state to refresh whether
    there are components available for update.

    Args:
      snapshot: snapshots.ComponentSnapshot, The snapshot pulled from the
        server.
      force: bool, True to force a recalculation of whether there are available
        updates, even if the snapshot revision has not changed.

    Returns:
      bool, True if there are now components to update, False otherwise.
    """
    if force or self.__last_update_check_revision != snapshot.revision:
      diff = self.__install_state.DiffCurrentState(snapshot)
      self.__updates_available = bool(diff.AvailableUpdates())
      self.__last_update_check_revision = snapshot.revision

    self.__last_update_check_date = time.time()
    self._SaveData()
    return self.__updates_available

  def SetFromIncompatibleSchema(self):
    """Sets that we just did an update check and found a new schema version."""
    self.__updates_available = True
    self.__last_update_check_revision = 0  # Doesn't matter
    self.__last_update_check_date = time.time()
    self._SaveData()
