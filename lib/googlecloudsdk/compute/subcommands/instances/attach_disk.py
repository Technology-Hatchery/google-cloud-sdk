# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for attaching a disk to an instance."""
from googlecloudapis.compute.v1 import compute_v1_messages as messages
from googlecloudsdk.compute.lib import base_classes


MODE_OPTIONS = ['ro', 'rw']


class AttachDisk(base_classes.BaseAsyncMutator):
  """Attaches a disk to an instance."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'name',
        metavar='INSTANCE',
        help='The name of the instance to attach the disk to.')

    parser.add_argument(
        '--device-name',
        help=('An optional name that indicates the disk name the guest '
              'operating system will see.'))

    parser.add_argument(
        '--disk',
        help='The name of the disk to attach to the instance.',
        required=True)

    mode = parser.add_argument(
        '--mode',
        choices=MODE_OPTIONS,
        default='rw',
        help='Specifies the mode of the disk.')
    mode.detailed_help = """\
        Specifies the mode of the disk. Supported options are ``ro'' for
        read-only and ``rw'' for read-write. If omitted, ``rw'' is used as
        a default. It is an error to attach a disk in read-write mode to
        more than one instance.
        """

    parser.add_argument(
        '--zone',
        help='The zone in which the instance and disk reside.',
        required=True)

  @property
  def service(self):
    return self.context['compute'].instances

  @property
  def method(self):
    return 'AttachDisk'

  @property
  def print_resource_type(self):
    return 'instances'

  def CreateRequests(self, args):
    """Returns a request for attaching a disk to an instance."""
    if args.mode == 'rw':
      mode = messages.AttachedDisk.ModeValueValuesEnum.READ_WRITE
    else:
      mode = messages.AttachedDisk.ModeValueValuesEnum.READ_ONLY

    request = messages.ComputeInstancesAttachDiskRequest(
        instance=args.name,
        project=self.context['project'],
        attachedDisk=messages.AttachedDisk(
            deviceName=args.device_name,
            mode=mode,
            source=self.context['uri-builder'].Build(
                'zones', args.zone, 'disks', args.disk),
            type=messages.AttachedDisk.TypeValueValuesEnum.PERSISTENT),
        zone=args.zone)

    return [request]


AttachDisk.detailed_help = {
    'brief': ('Attach a disk to an instance'),
    'DESCRIPTION': """\
        *{command}* is used to attach a disk to an instance. For example,

          $ compute instances attach-disk my-instance --disk my-disk
            --zone us-central1-a

        attaches the disk named ``my-disk'' to the instance named
        ``my-instance'' in zone ``us-central1-a''.
        """,
}
