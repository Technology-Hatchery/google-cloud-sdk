# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for creating backend services."""

from googlecloudapis.compute.v1 import compute_v1_messages as messages
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.compute.lib import base_classes


class Create(base_classes.BaseAsyncMutator):

  """Create a backend service."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--description',
        help='An optional, textual description for the backend service.')

    http_health_checks = parser.add_argument(
        '--http-health-check',
        required=True,
        help=('An HTTP health check object for checking the health of '
              'the backend service.'))
    http_health_checks.detailed_help = """\
        An HTTP health check object for checking the health of the
        backend service.
        """

    timeout = parser.add_argument(
        '--timeout',
        default='30s',
        type=arg_parsers.Duration(),
        help=('The amount of time to wait for a backend to respond to a '
              'request before considering the request failed.'))
    timeout.detailed_help = """\
        The amount of time to wait for a backend to respond to a
        request before considering the request failed. For example,
        specifying ``10s'' will give backends 10 seconds to respond to
        requests. Valid units for this flag are ``s'' for seconds,
        ``m'' for minutes, and ``h'' for hours.
        """

    parser.add_argument(
        '--port',
        default=80,
        type=int,
        help='The TCP port to use when connected to the backend.')

    parser.add_argument(
        'name',
        help='The name of the backend service.')

  @property
  def service(self):
    return self.context['compute'].backendServices

  @property
  def method(self):
    return 'Insert'

  @property
  def print_resource_type(self):
    return 'backendServices'

  def CreateRequests(self, args):
    health_checks = [
        self.context['uri-builder'].Build(
            'global', 'httpHealthChecks', args.http_health_check),
    ]

    request = messages.ComputeBackendServicesInsertRequest(
        backendService=messages.BackendService(
            description=args.description,
            healthChecks=health_checks,
            name=args.name,
            port=args.port,
            timeoutSec=args.timeout),
        project=self.context['project'])

    return [request]


Create.detailed_help = {
    'brief': 'Create a backend service',
    'DESCRIPTION': """
        *{command}* is used to create backend services. Backend
        services define groups of backends that can receive
        traffic. Each backend group has parameters that define the
        group's capacity (e.g., max CPU utilization, max queries per
        second, ...). URL maps define which requests are sent to which
        backend services.

        Backend services created through this command will start out
        without any backend groups. To add backend groups, use 'gcloud
        compute backend-services add-backend' or 'gcloud compute
        backend-services edit'.
        """,
}
