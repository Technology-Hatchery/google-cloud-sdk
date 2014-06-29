# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for creating target HTTP proxies."""

from googlecloudapis.compute.v1 import compute_v1_messages as messages
from googlecloudsdk.compute.lib import base_classes


class Create(base_classes.BaseAsyncMutator):
  """Create a target HTTP proxy."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--description',
        help='An optional, textual description for the target HTTP proxy.')

    url_map = parser.add_argument(
        '--url-map',
        required=True,
        help=('A reference to a URL map resource that defines the mapping of '
              'URLs to backend services.'))
    url_map.detailed_help = """\
        A reference to a URL map resource that defines the mapping of
        URLs to backend services. The URL map must exist and cannot be
        deleted while referenced by a target HTTP proxy.
        """

    parser.add_argument(
        'name',
        help='The name of the target HTTP proxy.')

  @property
  def service(self):
    return self.context['compute'].targetHttpProxies

  @property
  def method(self):
    return 'Insert'

  @property
  def print_resource_type(self):
    return 'targetHttpProxies'

  def CreateRequests(self, args):
    url_map_uri = self.context['uri-builder'].Build(
        'global', 'urlMaps', args.url_map)

    request = messages.ComputeTargetHttpProxiesInsertRequest(
        project=self.context['project'],
        targetHttpProxy=messages.TargetHttpProxy(
            description=args.description,
            name=args.name,
            urlMap=url_map_uri))
    return [request]


Create.detailed_help = {
    'brief': 'Create a target HTTP proxy',
    'DESCRIPTION': """
        *{command}* is used to create target HTTP proxies. A target
        HTTP proxy is referenced by one or more forwarding rules which
        define which packets the proxy is responsible for routing. The
        target HTTP proxy points to a URL map that defines the rules
        for routing the requests. The URL map's job is to map URLs to
        backend services which handle the actual requests.
        """,
}
