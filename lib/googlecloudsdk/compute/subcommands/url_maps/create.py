# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for creating URL maps."""

from googlecloudapis.compute.v1 import compute_v1_messages as messages
from googlecloudsdk.compute.lib import base_classes


class Create(base_classes.BaseAsyncMutator):
  """Create a URL map."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--default-service',
        required=True,
        help=('A backend service that will be used for requests for which this '
              'URL map has no mappings.'))
    parser.add_argument(
        '--description',
        help='An optional, textual description for the URL map.')

    parser.add_argument(
        'name',
        help='The name of the URL map.')

  @property
  def service(self):
    return self.context['compute'].urlMaps

  @property
  def method(self):
    return 'Insert'

  @property
  def print_resource_type(self):
    return 'urlMaps'

  def CreateRequests(self, args):
    default_service_uri = self.context['uri-builder'].Build(
        'global', 'backendServices', args.default_service)

    request = messages.ComputeUrlMapsInsertRequest(
        project=self.context['project'],
        urlMap=messages.UrlMap(
            defaultService=default_service_uri,
            description=args.description,
            name=args.name))
    return [request]


Create.detailed_help = {
    'brief': 'Create a URL map',
    'DESCRIPTION': """
        *{command}* is used to create URL maps which map HTTP and
        HTTPS request URLs to backend services. Mappings are done
        using a longest-match strategy.

        There are two components to a mapping: a host rule and a path
        matcher. A host rule maps one or more hosts to a path
        matcher. A path matcher maps request paths to backend
        services. For example, a host rule can map the hosts
        ``\\*.google.com'' and ``google.com'' to a path matcher called
        ``www''. The ``www'' path matcher in turn can map the path
        ``/search/*'' to the search backend service and everything
        else to a default backend service.

        Host rules and patch matchers can be added to the URL map
        after the map is created by using 'gcloud compute url-maps
        edit' or by using 'gcloud compute url-maps add-path-matcher'
        and 'gcloud compute url-maps add-host-rule'.
        """,
}
