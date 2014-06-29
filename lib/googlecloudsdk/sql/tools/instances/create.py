# Copyright 2013 Google Inc. All Rights Reserved.

"""Creates a new Cloud SQL instance."""
from apiclient import errors

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.sql import util


class Create(base.Command):
  """Creates a new Cloud SQL instance."""

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
        default='ON_DEMAND',
        help='The activation policy for this instance. This specifies when the '
        'instance should be activated and is applicable only when the '
        'instance state is RUNNABLE.')
    parser.add_argument(
        '--assign-ip',
        required=False,
        action='store_true',
        help='Specified if the instance must be assigned an IP address.')
    parser.add_argument(
        '--authorized-gae-apps',
        required=False,
        nargs='+',
        type=str,
        default=[],
        help='List of App Engine app IDs that can access this instance.')
    parser.add_argument(
        '--authorized-networks',
        required=False,
        nargs='+',
        type=str,
        default=[],
        help='The list of external networks that are allowed to connect to the'
        ' instance. Specified in CIDR notation, also known as \'slash\' '
        'notation (e.g. 192.168.100.0/24).')
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
        '--database-version',
        required=False,
        choices=['MYSQL_5_5', 'MYSQL_5_6'],
        default='MYSQL_5_5',
        help='The database engine type and version. Can be MYSQL_5_5 or '
        'MYSQL_5_6.')
    parser.add_argument(
        '--enable-bin-log',
        required=False,
        action='store_true',
        help='Specified if binary log should be enabled. If backup '
        'configuration is disabled, binary log must be disabled as well.')
    parser.add_argument(
        '--follow-gae-app',
        required=False,
        help='The App Engine app this instance should follow. It must be in '
        'the same region as the instance.')
    parser.add_argument(
        '--gce-zone',
        required=False,
        help='The preferred Compute Engine zone (e.g. us-central1-a, '
        'us-central1-b, etc.).')
    parser.add_argument(
        'instance',
        help='Cloud SQL instance ID.')
    parser.add_argument(
        '--pricing-plan',
        '-p',
        required=False,
        choices=['PER_USE', 'PACKAGE'],
        default='PER_USE',
        help='The pricing plan for this instance.')
    parser.add_argument(
        '--region',
        required=False,
        choices=['us-east1', 'europe-west1'],
        default='us-east1',
        help='The geographical region. Can be us-east1 or europe-west1.')
    parser.add_argument(
        '--replication',
        required=False,
        choices=['SYNCHRONOUS', 'ASYNCHRONOUS'],
        default='SYNCHRONOUS',
        help='The type of replication this instance uses.')
    parser.add_argument(
        '--require-ssl',
        required=False,
        action='store_true',
        help='Specified if users connecting over IP must use SSL.')
    parser.add_argument(
        '--tier',
        '-t',
        required=False,
        default='D1',
        help='The tier of service for this instance, for example D0, D1.')
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

  def SetDatabaseFlags(self, settings, database_flags):
    flags_list = []

    for (name, value) in database_flags.items():
      if value:
        flags_list.append({'name': name, 'value': value})
      else:
        flags_list.append({'name': name})

    settings['databaseFlags'] = flags_list

  def Run(self, args):
    """Creates a new Cloud SQL instance.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      A dict object representing the operations resource describing the create
      operation if the create was successful.
    Raises:
      HttpException: A http error response was received while executing api
          request.
      ToolException: An error other than http error occured while executing the
          command.
    """
    sql = self.context['sql']
    instance_id = util.GetInstanceIdWithoutProject(args.instance)
    project_id = util.GetProjectId(args.instance)
    activation_policy = args.activation_policy
    assign_ip = args.assign_ip
    authorized_gae_apps = args.authorized_gae_apps
    authorized_networks = args.authorized_networks
    database_flags = args.database_flags
    database_version = args.database_version
    enable_bin_log = args.enable_bin_log
    follow_gae_app = args.follow_gae_app
    gce_zone = args.gce_zone
    pricing_plan = args.pricing_plan
    region = args.region
    replication = args.replication
    require_ssl = args.require_ssl
    tier = args.tier

    backup_start_time = args.backup_start_time
    no_backup = args.no_backup
    settings = {}
    settings['tier'] = tier
    settings['pricingPlan'] = pricing_plan
    settings['replicationType'] = replication
    settings['activationPolicy'] = activation_policy
    settings['authorizedGaeApplications'] = authorized_gae_apps
    location_preference = {}
    if follow_gae_app:
      location_preference['followGaeApplication'] = follow_gae_app
    if gce_zone:
      location_preference['zone'] = gce_zone
    settings['locationPreference'] = location_preference
    ip_configuration = {'enabled': assign_ip,
                        'requireSsl': require_ssl,
                        'authorizedNetworks': authorized_networks}
    settings['ipConfiguration'] = [ip_configuration]

    if no_backup:
      if backup_start_time or enable_bin_log:
        raise exceptions.ToolException('Argument --no-backup not allowed with'
                                       ' --backup-start-time or '
                                       '--enable_bin_log')
      settings['backupConfiguration'] = [{'startTime': '00:00',
                                          'enabled': 'False'}]

    if backup_start_time:
      backup_config = [{'startTime': backup_start_time,
                        'enabled': 'True',
                        'binaryLogEnabled': enable_bin_log}]
      settings['backupConfiguration'] = backup_config

    if database_flags:
      self.SetDatabaseFlags(settings, database_flags)


    body = {'instance': instance_id, 'project': project_id, 'region': region,
            'databaseVersion': database_version, 'settings': settings}
    request = sql.instances().insert(project=project_id,
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
      create operation if the create was successful.
    """
    printer = util.PrettyPrinter(0)
    printer.Print('Result of the create operation:')
    printer.PrintOperation(result)
