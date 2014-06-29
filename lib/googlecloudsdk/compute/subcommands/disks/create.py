# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for creating disks."""
from googlecloudapis.compute.v1 import compute_v1_messages as messages
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.compute.lib import base_classes
from googlecloudsdk.compute.lib import constants
from googlecloudsdk.compute.lib import image_utils

_DEFAULT_DISK_SIZE_GB = 200


class CreateDisks(base_classes.BaseAsyncMutator):
  """Create Google Compute Engine persistent disks."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--description',
        help=(
            'An optional, textual description for the disks being created.'))

    size = parser.add_argument(
        '--size',
        type=arg_parsers.BinarySize(lower_bound='1GB'),
        help='Indicates the size of the disks.')
    size.detailed_help = """\
        Indicates the size of the disks. The value must be a whole
        number followed by a size unit of ``KB'' for kilobyte, ``MB''
        for megabyte, ``GB'' for gigabyte, or ``TB'' for terabyte. For
        example, ``10GB'' will produce 10 gigabyte disks. If omitted,
        a default size of 200 GB is used. The minimum size a disk can
        have is 1 GB. Disk size must be a multiple of 1 GB.
        """

    parser.add_argument(
        'names',
        metavar='NAME',
        nargs='+',
        help='The names of the disks to create.')

    source_group = parser.add_mutually_exclusive_group()

    def AddSourceImageHelp():
      return """\
          A source image to apply to the disks being created.
          +
          {alias_table}
          +
          This flag is mutually exclusive with ``--source-snapshot''.
          """.format(alias_table=image_utils.GetImageAliasTable())

    source_image = source_group.add_argument(
        '--source-image',
        help='A source image to apply to the disks being created.')
    source_image.detailed_help = AddSourceImageHelp

    source_snapshot = source_group.add_argument(
        '--source-snapshot',
        help='A source snapshot used to create the disks.')
    source_snapshot.detailed_help = """\
        A source snapshot used to create the disks. It is safe to
        delete a snapshot after a disk has been created from the
        snapshot. In such cases, the disks will no longer reference
        the deleted snapshot. To get a list of snapshots in your
        current project, run 'gcloud compute snapshots list'. A
        snapshot from an existing disk can be created using the
        'gcloud compute disks snapshot' command. This flag is mutually
        exclusive with ``--source-image''.
        """

    parser.add_argument(
        '--zone',
        help='The zone to create the disks in.',
        required=True)

  @property
  def service(self):
    return self.context['compute'].disks

  @property
  def method(self):
    return 'Insert'

  @property
  def print_resource_type(self):
    return 'disks'

  def CreateRequests(self, args):
    """Returns a list of requests necessary for adding disks."""

    if args.size:
      if args.size % constants.BYTES_IN_ONE_GB != 0:
        raise exceptions.ToolException(
            'disk size must be a multiple of 1 GB; did you mean "{0}GB"?'
            .format(args.size / constants.BYTES_IN_ONE_GB + 1))
      size_gb = args.size / constants.BYTES_IN_ONE_GB
    else:
      size_gb = None

    if not size_gb and not args.source_snapshot and not args.source_image:
      size_gb = _DEFAULT_DISK_SIZE_GB

    requests = []

    if args.source_snapshot:
      source_snapshot_uri = self.context['uri-builder'].Build(
          'global', 'snapshots', args.source_snapshot)
    else:
      source_snapshot_uri = None

    if args.source_image:
      source_image_uri = image_utils.ExpandImage(
          args.source_image, self.context['uri-builder'])
    else:
      source_image_uri = None

    for name in args.names:
      request = messages.ComputeDisksInsertRequest(
          disk=messages.Disk(
              name=name,
              description=args.description,
              sizeGb=size_gb,
              sourceSnapshot=source_snapshot_uri),
          project=self.context['project'],
          sourceImage=source_image_uri,
          zone=args.zone)
      requests.append(request)

    return requests


CreateDisks.detailed_help = {
    'brief': 'Create Google Compute Engine persistent disks',
    'DESCRIPTION': """\
        *{command}* creates one or more Google Compute Engine
        persistent disks. When creating virtual machine instances,
        disks can be attached to the instances through the
        'gcloud compute instances create' command. Disks can also be
        attached to instances that are already running using
        'gloud compute instances attach-disk'.

        Disks are zonal resources, so they reside in a particular zone
        for their entire lifetime. The contents of a disk can be moved
        to a different zone by snapshotting the disk (using
        'gcloud compute disks snapshot') and creating a new disk using
        ``--source-snapshot'' in the desired zone.

        When creating disks, be sure to include the ``--zone'' option:

          $ {command} my-disk-1 my-disk-2 --zone us-east1-a
        """,
}
