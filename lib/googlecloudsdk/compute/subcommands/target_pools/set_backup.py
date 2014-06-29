# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for setting a backup target pool."""
from googlecloudapis.compute.v1 import compute_v1_messages as messages
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.compute.lib import base_classes


class SetBackup(base_classes.BaseAsyncMutator):
  """Set a backup pool for a target pool."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--backup-pool',
        nargs='?',
        help=('Name of the target pool that will serve as backup. '
              'If this flag is provided without a value, the existing '
              'backup pool is removed.'),
        required=True)
    parser.add_argument(
        '--region',
        help='The region of the target pool.',
        required=True)
    parser.add_argument(
        '--failover-ratio',
        type=float,
        help=('The new failover ratio value for the target pool. '
              'This must be a float in the range of [0, 1].'))

    parser.add_argument(
        'name',
        help='The name of the target pool for which to set the backup pool.')

  @property
  def service(self):
    return self.context['compute'].targetPools

  @property
  def method(self):
    return 'SetBackup'

  @property
  def print_resource_type(self):
    return 'targetPools'

  def CreateRequests(self, args):
    """Returns a request necessary for setting a backup target pool."""

    if args.backup_pool:
      backup_pool_uri = self.context['uri-builder'].Build(
          'regions', args.region, 'targetPools', args.backup_pool)
      target_reference = messages.TargetReference(
          target=backup_pool_uri)
    else:
      target_reference = messages.TargetReference()

    if args.backup_pool and args.failover_ratio is None:
      raise calliope_exceptions.ToolException(
          '--failover-ratio must be provided when setting a backup pool')

    if args.failover_ratio is not None and (
        args.failover_ratio < 0 or args.failover_ratio > 1):
      raise calliope_exceptions.ToolException(
          '--failover-ratio must be a number between 0 and 1, inclusive')

    request = messages.ComputeTargetPoolsSetBackupRequest(
        targetPool=args.name,
        targetReference=target_reference,
        failoverRatio=args.failover_ratio,
        region=args.region,
        project=self.context['project'])

    return [request]


SetBackup.detailed_help = {
    'brief': 'Set a backup pool for a target pool',
    'DESCRIPTION': """\
        *{command}* is used to set a backup target pool for a primary
        target pool, which defines the fallback behavior of the primary
        pool. If the ratio of the healthy instances in the primary pool
        is at or below the specified ``--failover-ratio value'', then traffic
        arriving at the load-balanced IP address will be directed to the
        backup pool.
        """,
    'EXAMPLES': """\
        To cause ``my-target-pool'' (in region ``us-central1'') to fail over
        to ``my-backup-pool'' when more than half of my-target-pool's
        instances are unhealthy, run:

          $ {command} my-target-pool \\
              --backup-pool my-backup-pool --failover-ratio 0.5 \\
              --region us-central1

        To remove ``my-backup-pool'' as a backup to ``my-target-pool'', run:

          $ {command} my-target-pool \\
              --backup-pool \\
              --region us-central1
        """,
}
