# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for creating images."""
from googlecloudapis.compute.v1 import compute_v1_messages as messages
from googlecloudsdk.compute.lib import base_classes


class CreateImages(base_classes.BaseAsyncMutator):
  """Create Google Compute Engine images."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--description',
        help=('An optional, textual description for the image being created.'))

    parser.add_argument(
        '--source-uri',
        required=True,
        help=('The full Google Cloud Storage URL where the disk image is '
              'stored.'))

    parser.add_argument(
        'name',
        metavar='NAME',
        help='The name of the image to create.')

  @property
  def service(self):
    return self.context['compute'].images

  @property
  def method(self):
    return 'Insert'

  @property
  def print_resource_type(self):
    return 'images'

  def CreateRequests(self, args):
    """Returns a list of requests necessary for adding images."""
    if args.source_uri.startswith('gs://'):
      source_uri = ('http://storage.googleapis.com/' +
                    args.source_uri[len('gs://'):])
    else:
      source_uri = args.source_uri

    request = messages.ComputeImagesInsertRequest(
        image=messages.Image(
            name=args.name,
            description=args.description,
            rawDisk=messages.Image.RawDiskValue(source=source_uri),
            sourceType=messages.Image.SourceTypeValueValuesEnum.RAW),
        project=self.context['project'])

    return [request]


CreateImages.detailed_help = {
    'brief': 'Create Google Compute Engine images',
    'DESCRIPTION': """\
        *{command}* is used to create custom disk images.
        The resulting image can be provided during instance or disk creation
        so that the instance attached to the resulting disks has access
        to a known set of software or files from the image.
        """,
}
