# Copyright 2013 Google Inc. All Rights Reserved.

"""Higher level functions to support updater operations at the CLI level."""

import os
import subprocess
import sys
import textwrap

from googlecloudsdk.core import config
from googlecloudsdk.core import log
from googlecloudsdk.core import metrics
from googlecloudsdk.core import properties
from googlecloudsdk.core.updater import installers
from googlecloudsdk.core.updater import local_state
from googlecloudsdk.core.updater import schemas
from googlecloudsdk.core.updater import snapshots
from googlecloudsdk.core.util import console_io
from googlecloudsdk.core.util import files as file_utils
from googlecloudsdk.core.util import platforms


class Error(Exception):
  """Base exception for the update_manager module."""
  pass


class InvalidSDKRootError(Error):
  """Error for when the root of the Cloud SDK is invalid or cannot be found."""
  pass


class InvalidCWDError(Error):
  """Error for when your current working directory prevents an operation."""
  pass


class InvalidComponentSnapshotURLError(Error):
  """Error for when the components URL is invalid or cannot be found."""
  pass


class InvalidComponentSourceURLError(Error):
  """Error for when a single component's URL is invalid or cannot be found."""
  pass


class BadSDKPermissionsError(Error):
  """Error for problems with permissions when accessing SDK files."""
  pass


class InvalidComponentError(Error):
  """Error for when a given component id is not valid for the operation."""
  pass


class NoBackupError(Error):
  """Error for when you try to restore a backup but one does not exist."""
  pass


class ReinstallationFailedError(Error):
  """Error for when performing a reinstall fails."""
  pass


class UpdaterDisableError(Error):
  """Error for when an update is attempted but it is disallowed."""
  pass


def _RaisesBadSDKPermissionsError(func):
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
    except local_state.PermissionsError as e:
      raise BadSDKPermissionsError(e)
  return _TryFunc


class UpdateManager(object):
  """Main class for performing updates for the Cloud SDK."""

  UPDATE_CHECK_FREQUENCY_IN_SECONDS = 86400  # once a day
  BIN_DIR_NAME = 'bin'

  def __init__(self, sdk_root=None, url=None, platform_filter=None,
               out_stream=None):
    """Creates a new UpdateManager.

    Args:
      sdk_root: str, The path to the root directory of the Cloud SDK is
        installation.  If None, the updater will search for the install
        directory based on the current directory.
      url: str, The URL to get the latest component snapshot from.  If None,
        the default will be used.
      platform_filter: platforms.Platform, A platform that components must match
        in order to be considered for any operations.  If None, all components
        will match.
      out_stream: a file like object, The place to write more dynamic or
        interactive user output.  If not provided, sys.stdout will be used.

    Raises:
      InvalidSDKRootError: If the Cloud SDK root cannot be found.
    """

    if not url:
      url = properties.VALUES.component_manager.snapshot_url.Get()
    if url:
      log.warning('You are using an overridden snapshot URL: [%s]', url)
    else:
      url = config.INSTALLATION_CONFIG.snapshot_url

    self.__sdk_root = sdk_root
    if not self.__sdk_root:
      self.__sdk_root = local_state.InstallationState.FindSDKInstallRoot(
          os.path.dirname(__file__))
    if not self.__sdk_root:
      raise InvalidSDKRootError(
          'Could not locate the install root of the Cloud SDK.')
    self.__sdk_root = os.path.realpath(self.__sdk_root)
    self.__url = url
    self.__platform_filter = platform_filter
    self.__out_stream = out_stream if out_stream else log.out
    self.__text_wrapper = textwrap.TextWrapper(replace_whitespace=False,
                                               drop_whitespace=False)

  def __Write(self, msg='', word_wrap=False, stderr=False):
    """Writes the given message to the out stream with a new line.

    Args:
      msg: str, The message to write.
      word_wrap: bool, True to enable nicer word wrapper, False to just print
        the string as is.
      stderr: bool, True to write to stderr instead of the default out stream.
    """
    if word_wrap:
      msg = self.__text_wrapper.fill(msg)
    if stderr:
      sys.stderr.write(msg + '\n')
    else:
      self.__out_stream.write(msg + '\n')
    self.__out_stream.flush()

  def _CheckCWD(self, allow_no_backup=False):
    """Ensure that the command is not being run from within the SDK root.

    Args:
      allow_no_backup: bool, True if we want to allow the updater to run
        without creating a backup.  This lets us be in the root directory of the
        SDK and still do an update.  It is more fragile if there is a failure,
        so we only do it if necessary.

    Returns:
      bool, True if allow_no_backup was True and we are under the SDK root (so
        we should do a no backup update).

    Raises:
      InvalidCWDError: If the command is run from a directory within the SDK
        root.
    """
    cwd = os.path.realpath(os.getcwd())
    if not cwd.startswith(self.__sdk_root):
      # Outside of the root entirely, this is always fine.
      return False

    # We are somewhere under the install root.
    if (allow_no_backup and (self.__sdk_root == cwd or
                             self.__sdk_root == os.path.dirname(cwd))):
      # Backups are disable and we are in the root itself, or in a top level
      # directory.  This is OK since these directories won't ever be deleted.
      return True

    raise InvalidCWDError(
        'Your current working directory is inside the Cloud SDK install root:'
        ' {root}.  In order to perform this update, run the command from '
        'outside of this directory.'.format(root=self.__sdk_root))

  def _EnsureNotDisabled(self):
    """Prints an error and raises an Exception if the updater is disabled.

    The updater is disabled for installations that come from other package
    managers like apt-get or if the current user does not have permission
    to create or delete files in the SDK root directory.

    Raises:
      UpdaterDisableError: If the updater is disabled.
      BadSDKPermissionsError: If the caller has insufficient privilege.
    """
    if config.INSTALLATION_CONFIG.disable_updater:
      message = (
          'You cannot perform this action because the component manager has '
          'been disabled for this installation.  If you would like get the '
          'latest version of the Google Cloud SDK, please see our main '
          'download page at:\n  '
          + config.INSTALLATION_CONFIG.documentation_url + '\n')
      self.__Write(message, word_wrap=True, stderr=True)
      raise UpdaterDisableError(
          'The component manager is disabled for this installation')
    if (os.path.isdir(self.__sdk_root) and
        (not os.access(self.__sdk_root, os.X_OK) or
         not os.access(self.__sdk_root, os.W_OK))):
      message = (
          'You cannot perform this action because you do not have permission '
          'to modify the Google Cloud SDK installation directory [' +
          self.__sdk_root + '].')
      if (platforms.OperatingSystem.Current() ==
          platforms.OperatingSystem.WINDOWS):
        message += (
            ' Click the Google Cloud SDK Shell icon and re-run the command in '
            'that window, or re-run the command with elevated privileges by '
            'right-clicking cmd.exe and selecting "Run as Administrator".')
      else:
        message += (
            ' Re-run the command with sudo: sudo gcloud components ...')
      self.__Write(message, word_wrap=True, stderr=True)
      raise BadSDKPermissionsError(
          'Insufficient privilege to run component manager')

  def _GetInstallState(self):
    return local_state.InstallationState(self.__sdk_root)

  def _GetLatestSnapshot(self):
    return snapshots.ComponentSnapshot.FromURLs(*self.__url.split(','))

  def _GetStateAndDiff(self):
    install_state = self._GetInstallState()
    try:
      latest_snapshot = self._GetLatestSnapshot()
    except snapshots.URLFetchError as e:
      raise InvalidComponentSnapshotURLError(e)
    diff = install_state.DiffCurrentState(
        latest_snapshot, platform_filter=self.__platform_filter)
    return install_state, diff

  def GetCurrentVersionsInformation(self):
    """Get the current version for every installed component.

    Returns:
      {str:str}, A mapping from component id to version string.
    """
    current_state = self._GetInstallState()
    versions = {}
    installed_components = current_state.InstalledComponents()
    for component_id, component in installed_components.iteritems():
      if component.ComponentDefinition().is_configuration:
        continue
      versions[component_id] = component.VersionString()
    return versions

  @_RaisesBadSDKPermissionsError
  def PerformUpdateCheck(self, force=False):
    """Checks to see if a new snapshot has been released periodically.

    This method can be called as often as you'd like.  It will only actually
    check the server for updates if a certain amount of time has elapsed since
    the last check (or if force is True).  If updates are available, to any
    installed components, it will print a notification message.

    Args:
      force: bool, True to force a server check for updates, False to check only
        if the update frequency has expired.

    Returns:
      bool, True if updates are available, False otherwise.
    """
    if (config.INSTALLATION_CONFIG.disable_updater or
        properties.VALUES.component_manager.disable_update_check.GetBool()):
      return False

    install_state = self._GetInstallState()
    last_update_check = install_state.LastUpdateCheck()

    if not last_update_check.UpdatesAvailable():
      # Not time to check again
      if not force and (last_update_check.SecondsSinceLastUpdateCheck()
                        < UpdateManager.UPDATE_CHECK_FREQUENCY_IN_SECONDS):
        return False

      try:
        latest_snapshot = self._GetLatestSnapshot()
      except snapshots.IncompatibleSchemaVersionError:
        # The schema version of the snapshot is newer than what we know about,
        # it is definitely a newer version.
        last_update_check.SetFromIncompatibleSchema()
        return True
      updates_available = last_update_check.SetFromSnapshot(latest_snapshot)
      if not updates_available:
        return False

    self.__Write('\nThere are available updates for some Cloud SDK components.'
                 '  To install them, please run:', word_wrap=True, stderr=True)
    self.__Write(' $ gcloud components update\n', word_wrap=False, stderr=True)
    return True

  @_RaisesBadSDKPermissionsError
  def List(self, show_versions=False):
    """Lists all of the components and their current state.

    This pretty prints the list of components along with whether they are up
    to date, require an update, etc.

    Args:
      show_versions: bool, True to print versions in the table.  Defaults to
        False.

    Returns:
      The list of snapshots.ComponentDiffs for all components.
    """
    try:
      _, diff = self._GetStateAndDiff()
    except snapshots.IncompatibleSchemaVersionError as e:
      return self._DoFreshInstall(e)

    to_print = [diff.AvailableUpdates(), diff.Removed(),
                diff.AvailableToInstall(), diff.UpToDate()]

    self.__Write(
        'The following are the components available through the Google Cloud '
        'SDK.  You may choose to install one or more of the pre-configured '
        'packages (which contain everything you need to get started), and/or '
        'any of the individual components below.\n', word_wrap=True)

    self._PrintTable('Packages', False, to_print, lambda x: x.is_configuration)
    self.__Write('\n')
    self._PrintTable('Individual Components', show_versions, to_print,
                     lambda x: not x.is_configuration)

    self.__Write('\nTo install new components or update existing ones, run:',
                 word_wrap=True)
    self.__Write(' $ gcloud components update [component ids]')
    return diff.AllDiffs()

  def _PrintTable(self, title, show_versions, to_print, func):
    """Prints a table of updatable components.

    Args:
      title: str, The title for the table.
      show_versions: bool, True to print versions in the table.
      to_print: list(list(snapshots.ComponentDiff)), The available components
        divided by state.
      func: func(snapshots.ComponentDiff) -> bool, Decides whether the component
        should be printed.
    """
    printer = snapshots.ComponentDiff.TablePrinter(show_versions=show_versions)
    printer.SetTitle(title)
    rows = []
    for components in to_print:
      rows.extend([c.AsTableRow(show_versions=show_versions)
                   for c in components
                   if not c.is_hidden and func(c)])
    printer.Print(rows, output_stream=self.__out_stream)

  def _PrintPendingAction(self, components, action):
    """Prints info about components we are going to install or remove.

    Args:
      components: list(schemas.Component), The components that are going to be
        acted on.
      action: str, The verb to print for this set of components.
    """
    if not components:
      return

    header_string = 'The following components will be {action}:'.format(
        action=action)
    self.__Write(header_string)

    printer = schemas.Component.TablePrinter()
    rows = [c.AsTableRow() for c in components]
    printer.Print(rows, output_stream=self.__out_stream, indent=4)

  def _UpdateAndPrint(self, components, action, action_func):
    """Performs an update on a component while printing status.

    Args:
      components: [schemas.Component], The components that are going to be acted
        on.
      action: str, The action that is printed for this update.
      action_func: func, The function to call to actually do the update.  It
        takes a single argument which is the component id.
    """
    for component in components:
      self.__out_stream.write(
          '{action}: {name} ... '.format(
              action=action, name=component.details.display_name))
      self.__out_stream.flush()
      action_func(component.id)
      self.__Write('Done')
    self.__Write()

  def _InstallFunction(self, install_state, diff):
    def Inner(component_id):
      try:
        return install_state.Install(diff.latest, component_id)
      except installers.Error as e:
        raise InvalidComponentSourceURLError(e)
    return Inner

  @_RaisesBadSDKPermissionsError
  def Update(self, update_seed=None, allow_no_backup=False):
    """Performs an update of the given components.

    If no components are provided, it will attempt to update everything you have
    installed.

    Args:
      update_seed: list of str, A list of component ids to update.
      allow_no_backup: bool, True if we want to allow the updater to run
        without creating a backup.  This lets us be in the root directory of the
        SDK and still do an update.  It is more fragile if there is a failure,
        so we only do it if necessary.

    Raises:
      InvalidComponentError: If any of the given component ids do not exist.
    """
    self._EnsureNotDisabled()
    try:
      install_state, diff = self._GetStateAndDiff()
    except snapshots.IncompatibleSchemaVersionError as e:
      return self._DoFreshInstall(e)

    if update_seed:
      invalid_seeds = diff.InvalidUpdateSeeds(update_seed)
      if invalid_seeds:
        if os.environ.get('CLOUDSDK_REINSTALL_COMPONENTS'):
          # We are doing a reinstall.  Ignore any components that no longer
          # exist.
          update_seed = set(update_seed) - invalid_seeds
        else:
          raise InvalidComponentError(
              'The following components are unknown [{invalid_seeds}]'
              .format(invalid_seeds=', '.join(invalid_seeds)))
    else:
      update_seed = diff.current.components.keys()

    to_remove = diff.ToRemove(update_seed)
    to_install = diff.ToInstall(update_seed)

    self.__Write()
    if not to_remove and not to_install:
      self.__Write('All components are up to date.')
      install_state.LastUpdateCheck().SetFromSnapshot(diff.latest, force=True)
      return

    disable_backup = self._CheckCWD(allow_no_backup=allow_no_backup)
    self._PrintPendingAction(diff.DetailsForCurrent(to_remove - to_install),
                             'removed')
    self._PrintPendingAction(diff.DetailsForLatest(to_remove & to_install),
                             'updated')
    self._PrintPendingAction(diff.DetailsForLatest(to_install - to_remove),
                             'installed')
    self.__Write()

    if not console_io.PromptContinue():
      return

    components_to_install = diff.DetailsForLatest(to_install)
    components_to_remove = diff.DetailsForCurrent(to_remove)

    for c in components_to_install:
      metrics.Installs(c.id, c.version.version_string)

    if disable_backup:
      self.__Write('Performing in place update...\n')
      self._UpdateAndPrint(components_to_remove, 'Uninstalling',
                           install_state.Uninstall)
      self._UpdateAndPrint(components_to_install, 'Installing',
                           self._InstallFunction(install_state, diff))
    else:
      self.__Write('Creating update staging area...\n')
      staging_state = install_state.CloneToStaging()
      self._UpdateAndPrint(components_to_remove, 'Uninstalling',
                           staging_state.Uninstall)
      self._UpdateAndPrint(components_to_install, 'Installing',
                           self._InstallFunction(staging_state, diff))
      self.__Write('Creating backup and activating new installation...')
      install_state.ReplaceWith(staging_state)

    install_state.LastUpdateCheck().SetFromSnapshot(diff.latest, force=True)
    self.__Write('\nDone!\n')

    bad_commands = self.FindAllOldToolsOnPath()
    if bad_commands:
      log.warning("""\
There are older versions of Google Cloud Platform tools on your system PATH.
Please remove the following to avoid accidentally invoking these old tools:

{0}

""".format('\n'.join(bad_commands)))

  def FindAllOldToolsOnPath(self, path=None):
    """Searches the PATH for any old Cloud SDK tools.

    Args:
      path: str, A path to use instead of the PATH environment variable.

    Returns:
      {str}, The old executable paths.
    """
    bin_dir = os.path.realpath(
        os.path.join(self.__sdk_root, UpdateManager.BIN_DIR_NAME))
    bad_commands = set()
    if not os.path.exists(bin_dir):
      return bad_commands

    commands = [f for f in os.listdir(bin_dir)
                if os.path.isfile(os.path.join(bin_dir, f))]

    for command in commands:
      existing_paths = file_utils.SearchForExecutableOnPath(command, path=path)
      if existing_paths:
        this_tool = os.path.join(bin_dir, command)
        bad_commands.update(
            set(os.path.realpath(f) for f in existing_paths)
            - set([this_tool]))
    return bad_commands

  @_RaisesBadSDKPermissionsError
  def Remove(self, ids, allow_no_backup=False):
    """Uninstalls the given components.

    Args:
      ids: list of str, The component ids to uninstall.
      allow_no_backup: bool, True if we want to allow the updater to run
        without creating a backup.  This lets us be in the root directory of the
        SDK and still do an update.  It is more fragile if there is a failure,
        so we only do it if necessary.

    Raises:
      InvalidComponentError: If any of the given component ids are not
        installed or cannot be removed.
    """
    self._EnsureNotDisabled()
    if not ids:
      return

    install_state = self._GetInstallState()
    snapshot = install_state.Snapshot()
    id_set = set(ids)
    not_installed = id_set - set(snapshot.components.keys())
    if not_installed:
      raise InvalidComponentError(
          'The following components are not currently installed [{components}]'
          .format(components=', '.join(not_installed)))

    required_components = set(
        c_id for c_id, component in snapshot.components.iteritems()
        if c_id in id_set and component.is_required)
    if required_components:
      raise InvalidComponentError(
          ('The following components are required and cannot be removed '
           '[{components}]')
          .format(components=', '.join(required_components)))

    to_remove = snapshot.ConsumerClosureForComponents(ids)
    if not to_remove:
      self.__Write('No components to remove.\n')
      return

    disable_backup = self._CheckCWD(allow_no_backup=allow_no_backup)
    components_to_remove = sorted(snapshot.ComponentsFromIds(to_remove),
                                  key=lambda c: c.details.display_name)
    self._PrintPendingAction(components_to_remove, 'removed')
    self.__Write()

    if not console_io.PromptContinue():
      return

    if disable_backup:
      self.__Write('Performing in place update...\n')
      self._UpdateAndPrint(components_to_remove, 'Uninstalling',
                           install_state.Uninstall)
    else:
      self.__Write('Creating update staging area...\n')
      staging_state = install_state.CloneToStaging()
      self._UpdateAndPrint(components_to_remove, 'Uninstalling',
                           staging_state.Uninstall)
      self.__Write('Creating backup and activating new installation...')
      install_state.ReplaceWith(staging_state)

    self.__Write('\nDone!\n')

  @_RaisesBadSDKPermissionsError
  def Restore(self):
    """Restores the latest backup installation of the Cloud SDK.

    Raises:
      NoBackupError: If there is no valid backup to restore.
    """
    self._EnsureNotDisabled()
    install_state = self._GetInstallState()
    if not install_state.HasBackup():
      raise NoBackupError('There is currently no backup to restore.')

    self._CheckCWD()

    if not console_io.PromptContinue(
        message='Your Cloud SDK installation will be restored to its previous '
        'state.'):
      return

    self.__Write('Restoring backup...\n')
    install_state.RestoreBackup()

    self.__Write('\nDone!\n')

  @_RaisesBadSDKPermissionsError
  def _DoFreshInstall(self, e):
    """Do a reinstall of what we have based on a fresh download of the SDK.

    Args:
      e: snapshots.IncompatibleSchemaVersionError, The exception we got with
        information about the new schema version.
    """
    self._EnsureNotDisabled()
    if os.environ.get('CLOUDSDK_REINSTALL_COMPONENTS'):
      # We are already reinstalling but got here somehow.  Something is very
      # wrong and we want to avoid the infinite loop.
      self._RaiseReinstallationFailedError()

    # Print out an arbitrary message that we wanted to show users for this
    # udpate.
    message = e.schema_version.message
    if message:
      self.__Write(msg=message, word_wrap=True)

    # We can decide that for some reason we just never want to update past this
    # version of the schema.
    if e.schema_version.no_update:
      return

    answer = console_io.PromptContinue(
        message='\nThe component manager must perform a self update before you '
        'can continue.  It and all components will be updated to their '
        'latest versions.')
    if not answer:
      return

    self._CheckCWD()
    install_state = self._GetInstallState()
    self.__Write('Downloading and extracting updated components...\n')
    download_url = e.schema_version.url
    try:
      staging_state = install_state.CreateStagingFromDownload(download_url)
    except local_state.Error:
      log.error('An updated Cloud SDK failed to download')
      self._RaiseReinstallationFailedError()

    # shell out to install script
    installed_component_ids = sorted(install_state.InstalledComponents().keys())
    env = dict(os.environ)
    env['CLOUDSDK_REINSTALL_COMPONENTS'] = ','.join(
        installed_component_ids)
    installer_path = os.path.join(staging_state.sdk_root,
                                  'bin', 'bootstrapping', 'install.py')
    p = subprocess.Popen([sys.executable, '-S', installer_path], env=env)
    ret_val = p.wait()
    if ret_val:
      self._RaiseReinstallationFailedError()

    self.__Write('Creating backup and activating new installation...')
    install_state.ReplaceWith(staging_state)

    self.__Write('\nDone!\n')

  def _RaiseReinstallationFailedError(self):
    raise ReinstallationFailedError(
        'An error occurred while reinstalling the Cloud SDK.  Please download'
        ' a new copy from: {url}'.format(
            url=config.INSTALLATION_CONFIG.documentation_url))
