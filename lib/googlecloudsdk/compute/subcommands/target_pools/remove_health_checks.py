# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for removing health checks from target pools."""
from googlecloudapis.compute.v1 import compute_v1_messages as messages
from googlecloudsdk.compute.lib import base_classes


class RemoveHealthChecks(base_classes.BaseAsyncMutator):
  """Remove a health check from a target pool."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--http-health-check',
        help=('Specifies an HTTP health check object to remove from the '
              'target pool.'),
        metavar='HEALTH_CHECK',
        required=True)

    parser.add_argument(
        '--region',
        help='The region of the target pool.',
        required=True)

    parser.add_argument(
        'name',
        help=('The name of the target pool from which to remove the '
              'health check.'))

  @property
  def service(self):
    return self.context['compute'].targetPools

  @property
  def method(self):
    return 'RemoveHealthCheck'

  @property
  def print_resource_type(self):
    return 'targetPools'

  def CreateRequests(self, args):
    http_health_check_uri = self.context['uri-builder'].Build(
        'global', 'httpHealthChecks', args.http_health_check)

    request = messages.ComputeTargetPoolsRemoveHealthCheckRequest(
        region=args.region,
        project=self.context['project'],
        targetPool=args.name,
        targetPoolsRemoveHealthCheckRequest=(
            messages.TargetPoolsRemoveHealthCheckRequest(
                healthChecks=[messages.HealthCheckReference(
                    healthCheck=http_health_check_uri)])))

    return [request]


RemoveHealthChecks.detailed_help = {
    'brief': 'Remove an HTTP health check from a target pool',
    'DESCRIPTION': """\
        *{command}* is used to remove an HTTP health check
        from a target pool. Health checks are used to determine
        the health status of instances in the target pool. For more
        information on health checks and load balancing, see
        link:https://developers.google.com/compute/docs/load-balancing/[].
        """,
}
