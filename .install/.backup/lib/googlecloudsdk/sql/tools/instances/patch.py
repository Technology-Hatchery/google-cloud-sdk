# Copyright 2013 Google Inc. All Rights Reserved.

"""Updates the settings of a Cloud SQL instance."""
from apiclient import errors

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core.util import console_io
from googlecloudsdk.sql import util


class Patch(base.Command):
  """Updates the settings of a Cloud SQL instance."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Please add arguments in alphabetical order except for no- or a clear-
    pair for that argument which can follow the argument itself.
    Args:
      parser: An argparse parser that you can use it to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    parser.add_argument(
        '--activation-policy',
        required=False,
        choices=['ALWAYS', 'NEVER', 'ON_DEMAND'],
        help='The activation policy for this instance. This specifies when the '
        'instance should be activated and is applicable only when the '
        'instance state is RUNNABLE.')
    parser.add_argument(
        '--assign-ip',
        required=False,
        action='store_true',
        help='Specified if the instance must be assigned an IP address.')
    parser.add_argument(
        '--no-assign-ip',
        required=False,
        action='store_true',
        help='Specified if the assigned IP address must be revoked.')
    parser.add_argument(
        '--authorized-gae-apps',
        required=False,
        nargs='+',
        type=str,
        help='A list of App Engine app IDs that can access this instance.')
    parser.add_argument(
        '--clear-gae-apps',
        required=False,
        action='store_true',
        help=('Specified to clear the list of App Engine apps that can access '
              'this instance.'))
    parser.add_argument(
        '--authorized-networks',
        required=False,
        nargs='+',
        type=str,
        help='The list of external networks that are allowed to connect to the '
        'instance. Specified in CIDR notation, also known as \'slash\' '
        'notation (e.g. 192.168.100.0/24).')
    parser.add_argument(
        '--clear-authorized-networks',
        required=False,
        action='store_true',
        help='Clear the list of external networks that are allowed to connect '
        'to the instance.')
    parser.add_argument(
        '--backup-start-time',
        required=False,
        help='The start time of daily backups, specified in the 24 hour format '
        '- HH:MM, in the UTC timezone.')
    parser.add_argument(
        '--no-backup',
        required=False,
        action='store_true',
        help='Specified if daily backup should be disabled.')
    parser.add_argument(
        '--database-flags',
        required=False,
        nargs='+',
        action=arg_parsers.AssociativeList(),
        help='A space-separated list of database flags to set on the instance. '
        'Use an equals sign to separate flag name and value. Flags without '
        'values, like skip_grant_tables, can be written out without a value '
        'after, e.g., `skip_grant_tables=`. Use on/off for '
        'booleans. View the Instance Resource API for allowed flags. '
        '(e.g., `--database-flags max_allowed_packet=55555 skip_grant_tables= '
        'log_output=1`)')
    parser.add_argument(
        '--clear-database-flags',
        required=False,
        action='store_true',
        help='Clear the database flags set on the instance. '
        'WARNING: Instance will be restarted.')
    parser.add_argument(
        '--enable-bin-log',
        required=False,
        action='store_true',
        help='Specified if binary log should be enabled. If backup '
        'configuration is disabled, binary log should be disabled as well.')
    parser.add_argument(
        '--no-enable-bin-log',
        required=False,
        action='store_true',
        help='Specified if binary log should be disabled.')
    parser.add_argument(
        '--follow-gae-app',
        required=False,
        help='The App Engine app this instance should follow. It must be in '
        'the same region as the instance. '
        'WARNING: Instance may be restarted.')
    parser.add_argument(
        '--gce-zone',
        required=False,
        help='The preferred Compute Engine zone (e.g. us-central1-a, '
        'us-central1-b, etc.). '
        'WARNING: Instance may be restarted.')
    parser.add_argument(
        'instance',
        help='Cloud SQL instance ID.')
    parser.add_argument(
        '--pricing-plan',
        '-p',
        required=False,
        choices=['PER_USE', 'PACKAGE'],
        help='The pricing plan for this instance.')
    parser.add_argument(
        '--replication',
        required=False,
        choices=['SYNCHRONOUS', 'ASYNCHRONOUS'],
        help='The type of replication this instance uses.')
    parser.add_argument(
        '--require-ssl',
        required=False,
        action='store_true',
        help='Specified if the mysqld should default to \'REQUIRE X509\' for '
        'users connecting over IP.')
    parser.add_argument(
        '--no-require-ssl',
        required=False,
        action='store_true',
        help='Specified if the mysqld should not default to \'REQUIRE X509\' '
        'for users connecting over IP.')
    parser.add_argument(
        '--tier',
        '-t',
        required=False,
        help='The tier of service for this instance, for example D0, D1. '
        'WARNING: Instance will be restarted.')

  def GetExistingBackupConfig(self, instance_id):
    """Returns the existing backup configuration of the given instance.

    Args:
      instance_id: The Cloud SQL instance id.
    Returns:
      A dict object that represents the backup configuration of the given
      instance or None if no existing configuration exists.
    """
    instance = self.command.ParentGroup().ParentGroup().instances.get(
        instance=instance_id)
    backup_config = None

    # At this point we support only one backup-config. So, we just use that
    # id.
    if 'backupConfiguration' in instance['settings']:
      backup_id = instance['settings']['backupConfiguration'][0]['id']
      start_time = (instance['settings']['backupConfiguration'][0]['startTime'])
      enabled = (instance['settings']['backupConfiguration'][0]['enabled'])
      bin_log = (instance['settings']['backupConfiguration'][0]
                 ['binaryLogEnabled'])
      backup_config = {'startTime': start_time, 'enabled': enabled,
                       'id': backup_id, 'binaryLogEnabled': bin_log}

    return backup_config

  def SetLocationPreference(self, settings, follow_gae_app, gce_zone):
    location_preference = {}
    if follow_gae_app:
      location_preference['followGaeApplication'] = follow_gae_app
    if gce_zone:
      location_preference['zone'] = gce_zone
    if follow_gae_app or gce_zone:
      settings['locationPreference'] = location_preference

  def SetIpConfiguration(self, settings, assign_ip, no_assign_ip,
                         authorized_networks, clear_authorized_networks,
                         require_ssl, no_require_ssl):
    ip_configuration = {}
    if assign_ip or no_assign_ip:
      ip_configuration['enabled'] = bool(assign_ip)
    if authorized_networks or clear_authorized_networks:
      ip_configuration['authorizedNetworks'] = list(authorized_networks or [])
    if require_ssl or no_require_ssl:
      ip_configuration['requireSsl'] = bool(require_ssl)
    if (assign_ip or no_assign_ip or authorized_networks or
        clear_authorized_networks or require_ssl or no_require_ssl):
      settings['ipConfiguration'] = ip_configuration

  def SetBackupConfiguration(self, settings, instance_id, backup_start_time,
                             enable_bin_log, no_enable_bin_log, no_backup):
    """Constructs the backup configuration sub-object for the patch method.

    Args:
      settings: The settings dict where the backup configuration should be set.
      instance_id: The Cloud SQL instance id.
      backup_start_time: Backup start time to be set.
      enable_bin_log: Set if bin log must be enabled.
      no_enable_bin_log: Set if bin log must be disabled.
      no_backup: Set if backup must be disabled.
    """
    backup_config = self.GetExistingBackupConfig(instance_id) or {}

    # We have to explicitly populate the rest of the existing backup config
    # values for patch method because it will replace the entire
    # backupConfiguration value since it is a list.
    if no_backup:
      backup_config['enabled'] = False
    if backup_start_time:
      backup_config['startTime'] = backup_start_time
      backup_config['enabled'] = True
    if enable_bin_log:
      backup_config['binaryLogEnabled'] = True
    if no_enable_bin_log:
      backup_config['binaryLogEnabled'] = False
    if no_backup or backup_start_time or enable_bin_log or no_enable_bin_log:
      settings['backupConfiguration'] = [backup_config]

  def SetAuthorizedGaeApps(self, settings, authorized_gae_apps, clear_gae_apps):
    if authorized_gae_apps:
      settings['authorizedGaeApplications'] = authorized_gae_apps
    if clear_gae_apps:
      if authorized_gae_apps:
        raise exceptions.ToolException('Argument --clear-gae-apps not allowed '
                                       'with --authorized_gae_apps')
      settings['authorizedGaeApplications'] = None

  def SetDatabaseFlags(self, settings, database_flags, clear_database_flags):
    if database_flags:
      flags_list = []

      for (name, value) in database_flags.items():
        if value:
          flags_list.append({'name': name, 'value': value})
        else:
          flags_list.append({'name': name})

      settings['databaseFlags'] = flags_list

    if clear_database_flags:
      # TODO(user): Check that this should be None and not []
      settings['databaseFlags'] = None

  def Run(self, args):
    """Updates settings of a Cloud SQL instance using the patch api method.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      A dict object representing the operations resource describing the patch
      operation if the patch was successful.
    Raises:
      HttpException: A http error response was received while executing api
          request.
      ToolException: An error other than http error occured while executing the
          command.
    """
    sql = self.context['sql']
    instance_id = util.GetInstanceIdWithoutProject(args.instance)
    project_id = util.GetProjectId(args.instance)
    replication = args.replication
    tier = args.tier
    activation_policy = args.activation_policy
    assign_ip = args.assign_ip
    authorized_gae_apps = args.authorized_gae_apps
    authorized_networks = args.authorized_networks
    backup_start_time = args.backup_start_time
    clear_gae_apps = args.clear_gae_apps
    clear_authorized_networks = args.clear_authorized_networks
    enable_bin_log = args.enable_bin_log
    follow_gae_app = args.follow_gae_app
    gce_zone = args.gce_zone
    no_backup = args.no_backup
    no_assign_ip = args.no_assign_ip
    no_enable_bin_log = args.no_enable_bin_log
    no_require_ssl = args.no_require_ssl
    pricing_plan = args.pricing_plan
    require_ssl = args.require_ssl
    database_flags = args.database_flags
    clear_database_flags = args.clear_database_flags
    if assign_ip and no_assign_ip:
      raise exceptions.ToolException('Argument --assign-ip not allowed with '
                                     '--no-assign-ip')
    if authorized_networks and clear_authorized_networks:
      raise exceptions.ToolException('Argument --authorized-networks not '
                                     'allowed with --clear-authorized-networks')
    if backup_start_time and no_backup:
      raise exceptions.ToolException('Argument --backup-start-time not '
                                     'allowed with --no-backup')
    if enable_bin_log and no_enable_bin_log:
      raise exceptions.ToolException('Argument --enable-bin-log not allowed '
                                     'with --no-enable-bin-log')
    if follow_gae_app and gce_zone:
      raise exceptions.ToolException('Argument --gce-zone not allowed with '
                                     '--follow-gae-app')
    if require_ssl and no_require_ssl:
      raise exceptions.ToolException('Argument --require-ssl not allowed with '
                                     '--no-require-ssl')
    if database_flags and clear_database_flags:
      raise exceptions.ToolException('Argument --database-flags not allowed '
                                     'with --clear-database-flags')
    settings = {}
    if tier:
      settings['tier'] = tier
    if pricing_plan:
      settings['pricingPlan'] = pricing_plan
    if replication:
      settings['replicationType'] = replication
    if activation_policy:
      settings['activationPolicy'] = activation_policy

    self.SetLocationPreference(settings, follow_gae_app, gce_zone)
    self.SetIpConfiguration(settings, assign_ip, no_assign_ip,
                            authorized_networks, clear_authorized_networks,
                            require_ssl, no_require_ssl)
    self.SetBackupConfiguration(settings, instance_id, backup_start_time,
                                enable_bin_log, no_enable_bin_log, no_backup)
    self.SetAuthorizedGaeApps(settings, authorized_gae_apps, clear_gae_apps)
    self.SetDatabaseFlags(settings, database_flags, clear_database_flags)
    body = {'instance': instance_id, 'settings': settings}
    printer = util.PrettyPrinter(0)
    printer.Print('This command will change the instance settings.')
    printer.Print('All arrays must be fully-specified. '
                  'Any previous data in an array will be overwritten with the '
                  'given list.')
    printer.Print('The following JSON message will be used for the patch API '
                  'method.')
    printer.Print(str(body))

    if (tier or follow_gae_app or database_flags or clear_database_flags or
        gce_zone):
      if (follow_gae_app or gce_zone and not
          (tier or database_flags or clear_database_flags)):
        printer.Print('WARNING: This patch modifies the zone your instance '
                      'is set to run in, which may require it to be moved. '
                      'Submitting this patch will restart your instance '
                      'if it is running in a different zone.')
      else:
        printer.Print('WARNING: This patch modifies a value that requires '
                      'your instance to be restarted. Submitting this patch '
                      'will immediately restart your instance if it\'s '
                      'running.')

    if not console_io.PromptContinue():
      return util.QUIT
    request = sql.instances().patch(project=project_id,
                                    instance=instance_id,
                                    body=body)
    try:
      result = request.execute()
      operations = self.command.ParentGroup().ParentGroup().operations(
          instance=instance_id)
      operation = operations.get(operation=result['operation'])
      return operation
    except errors.HttpError as error:
      raise exceptions.HttpException(util.GetError(error))
    except errors.Error as error:
      raise exceptions.ToolException(error)

  def Display(self, unused_args, result):
    """Display prints information about what just happened to stdout.

    Args:
      unused_args: The same as the args in Run.
      result: A dict object representing the operations resource describing the
      patch operation if the patch was successful.
    """
    printer = util.PrettyPrinter(0)
    if result is not util.QUIT:
      printer.Print('Result of the patch operation:')
      printer.PrintOperation(result)
