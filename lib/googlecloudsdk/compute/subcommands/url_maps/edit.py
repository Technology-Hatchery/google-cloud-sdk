# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for modifying URL maps."""

from googlecloudapis.compute.v1 import compute_v1_messages as messages
from googlecloudsdk.compute.lib import base_classes


class Edit(base_classes.BaseEdit):
  """Modify URL maps."""

  @staticmethod
  def Args(parser):
    base_classes.BaseEdit.Args(parser)
    parser.add_argument(
        'name',
        help='The name of the URL map to modify.')

  @property
  def service(self):
    return self.context['compute'].urlMaps

  @property
  def print_resource_type(self):
    return 'urlMaps'

  @property
  def example_resource(self):
    uri_prefix = ('https://www.googleapis.com/compute/v1/projects/'
                  'my-project/global/backendServices/')
    return messages.UrlMap(
        name='site-map',
        defaultService=uri_prefix + 'default-service',
        hostRules=[
            messages.HostRule(
                hosts=['*.google.com', 'google.com'],
                pathMatcher='www'),
            messages.HostRule(
                hosts=['*.youtube.com', 'youtube.com', '*-youtube.com'],
                pathMatcher='youtube'),
        ],
        pathMatchers=[
            messages.PathMatcher(
                name='www',
                defaultService=uri_prefix + 'www-default',
                pathRules=[
                    messages.PathRule(
                        paths=['/search', '/search/*'],
                        service=uri_prefix + 'search'),
                    messages.PathRule(
                        paths=['/search/ads', '/search/ads/*'],
                        service=uri_prefix + 'ads'),
                    messages.PathRule(
                        paths=['/images'],
                        service=uri_prefix + 'images'),
                ]),
            messages.PathMatcher(
                name='youtube',
                defaultService=uri_prefix + 'youtube-default',
                pathRules=[
                    messages.PathRule(
                        paths=['/search', '/search/*'],
                        service=uri_prefix + 'youtube-search'),
                    messages.PathRule(
                        paths=['/watch', '/view', '/preview'],
                        service=uri_prefix + 'youtube-watch'),
                ]),
        ],
        tests=[
            messages.UrlMapTest(
                host='www.google.com',
                path='/search/ads/inline?q=flowers',
                service=uri_prefix + 'ads'),
            messages.UrlMapTest(
                host='youtube.com',
                path='/watch/this',
                service=uri_prefix + 'youtube-default'),
        ],
    )

  def GetGetRequest(self, args):
    return (
        self.service,
        'Get',
        messages.ComputeUrlMapsGetRequest(
            project=self.context['project'],
            urlMap=args.name))

  def GetSetRequest(self, args, replacement, _):
    return (
        self.service,
        'Update',
        messages.ComputeUrlMapsUpdateRequest(
            project=self.context['project'],
            urlMap=args.name,
            urlMapResource=replacement))


Edit.detailed_help = {
    'brief': 'Modify URL maps',
    'DESCRIPTION': """\
        *{command}* can be used to modify a URL map. The URL map
        resource is fetched from the server and presented in a text
        editor. After the file is saved and closed, this command will
        update the resource. Only fields that can be modified are
        displayed in the editor.

        The editor used to modify the resource is chosen by inspecting
        the ``EDITOR'' environment variable.
        """,
}
