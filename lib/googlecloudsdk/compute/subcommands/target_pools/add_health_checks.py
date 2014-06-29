# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for adding health checks to target pools."""
from googlecloudapis.compute.v1 import compute_v1_messages as messages
from googlecloudsdk.compute.lib import base_classes


class AddHealthChecks(base_classes.BaseAsyncMutator):
  """Add a health check to a target pool."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--http-health-check',
        help=('Specifies an HTTP health check object to add to the '
              'target pool.'),
        metavar='HEALTH_CHECK',
        required=True)

    parser.add_argument(
        '--region',
        help='The region of the target pool.',
        required=True)

    parser.add_argument(
        'name',
        help='The name of the target pool to which to add the health check.')

  @property
  def service(self):
    return self.context['compute'].targetPools

  @property
  def method(self):
    return 'AddHealthCheck'

  @property
  def print_resource_type(self):
    return 'targetPools'

  def CreateRequests(self, args):
    http_health_check_uri = self.context['uri-builder'].Build(
        'global', 'httpHealthChecks', args.http_health_check)

    request = messages.ComputeTargetPoolsAddHealthCheckRequest(
        region=args.region,
        project=self.context['project'],
        targetPool=args.name,
        targetPoolsAddHealthCheckRequest=(
            messages.TargetPoolsAddHealthCheckRequest(
                healthChecks=[messages.HealthCheckReference(
                    healthCheck=http_health_check_uri)])))

    return [request]


AddHealthChecks.detailed_help = {
    'brief': 'Add an HTTP health check to a target pool',
    'DESCRIPTION': """\
        *{command}* is used to add an HTTP health check
        to a target pool. Health checks are used to determine
        the health status of instances in the target pool. Only one
        health check can be attached to a target pool, so this command
        will fail if there as already a health check attached to the target
        pool. For more information on health checks and load balancing, see
        link:https://developers.google.com/compute/docs/load-balancing/[].
        """,
}
