# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for getting health status of backend(s) in a backend service."""

from googlecloudapis.compute.v1 import compute_v1_messages as messages
from googlecloudsdk.compute.lib import base_classes
from googlecloudsdk.compute.lib import request_helper


class GetHealth(base_classes.BaseGetter):
  """Get health status of backend(s) in an backend service."""

  @staticmethod
  def Args(parser):
    base_classes.BaseGetter.Args(parser, add_name_regex_arg=False)
    base_classes.AddFieldsFlag(parser, 'backendServiceGroupHealth')

    parser.add_argument(
        'name',
        help='The name of the backend service.')

  @property
  def service(self):
    return self.context['compute'].backendServices

  @property
  def print_resource_type(self):
    return 'backendServiceGroupHealth'

  def GetBackendService(self, args):
    """Fetches the backend service resource."""
    objects = list(request_helper.MakeRequests(
        requests=[(self.service,
                   'Get',
                   messages.ComputeBackendServicesGetRequest(
                       project=self.context['project'],
                       backendService=args.name
                       ))],
        http=self.context['http'],
        batch_url=self.context['batch-url']))
    return objects[0]

  def GetResources(self, args, errors):
    """Returns a list of backendServiceGroupHealth objects."""

    backend_service = self.GetBackendService(args)
    if not backend_service.backends:
      return []

    # Call GetHealth for each group in the backend service
    requests = []
    for backend in backend_service.backends:
      request_message = messages.ComputeBackendServicesGetHealthRequest(
          resourceGroupReference=messages.ResourceGroupReference(
              group=backend.group),
          project=self.context['project'],
          backendService=args.name)
      requests.append((self.service, 'GetHealth', request_message))

    return request_helper.MakeRequests(
        requests=requests,
        http=self.context['http'],
        batch_url=self.context['batch-url'])


GetHealth.detailed_help = {
    'brief': 'Get backend health statuses from a backend service',
    'DESCRIPTION': """
        *{command}* is used to request the current health status of
        instances in a backend service.  Every group in the service
        is checked and the health status of each configured instance
        is printed.

        If a group contains names of instance that don't exist or
        instances that haven't yet been pushed to the load-balancing
        system, they will not show up. Those that are listed as
        ``HEALTHY'' are able to receive load-balanced traffic. Those that
        are marked as ``UNHEALTHY'' are either failing the configured
        health-check or not responding to it.

        Since the health checks are performed continuously and in
        a distributed manner, the state returned by this command is
        the most recent result of a vote of several redundant health
        checks. Backend services that do not have a valid global
        forwarding rule referencing it will not be health checked and
        so will have no health status.
        """,
}

