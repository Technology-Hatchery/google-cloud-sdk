# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for creating instances."""
import collections

from googlecloudapis.compute.v1 import compute_v1_messages as messages
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.compute.lib import base_classes
from googlecloudsdk.compute.lib import constants
from googlecloudsdk.compute.lib import image_utils
from googlecloudsdk.compute.lib import metadata_utils


DISK_METAVAR = (
    'name=NAME [mode={ro,rw}] [boot={yes,no}] [device-name=DEVICE_NAME] '
    '[auto-delete={yes,no}]')

MIGRATION_OPTIONS = sorted(
    messages.Scheduling.OnHostMaintenanceValueValuesEnum.to_dict().keys())


class CreateInstances(base_classes.BaseAsyncMutator):
  """Create Google Compute Engine virtual machine instances."""

  @staticmethod
  def Args(parser):
    metadata_utils.AddMetadataArgs(parser)

    boot_disk_device_name = parser.add_argument(
        '--boot-disk-device-name',
        help='The name the guest operating system will see the boot disk as.')
    boot_disk_device_name.detailed_help = """\
        The name the guest operating system will see for the boot disk
        as. This option can only be specified when using
        ``--image''. When creating more than one instance, the value
        of the device name will apply to all of the instances' boot
        disks.
        """

    boot_disk_size = parser.add_argument(
        '--boot-disk-size',
        type=arg_parsers.BinarySize(lower_bound='10GB'),
        help='The size of the boot disk.')
    boot_disk_size.detailed_help = """\
        The size of the boot disk. This option can only be specified when using
        ``--image''. The value must be a whole number followed
        by a size unit of ``KB'' for kilobyte, ``MB'' for megabyte, ``GB'' for
        gigabyte, or ``TB'' for terabyte. For example, ``10GB'' will produce a
        10 gigabyte disk. If omitted, a default size of 200 GB is used. The
        minimum size a disk can have is 1 GB. Disk size must be a multiple
        of 1 GB. When creating more than one instance, the size will apply
        to all of the instances' boot disks.
        """

    parser.add_argument(
        '--no-boot-disk-auto-delete',
        action='store_true',
        help=('If provided, boot disks will not be automatically deleted '
              'when their instances are deleted.'))

    def AddImageHelp():
      return """\
          Specifies the boot image for the instances. For each
          instance, a new boot disk will be created from the given
          image. Each boot disk will have the same name as the
          instance.
          +
          {alias_table}
          +
          When using this option, ``--boot-disk-device-name'' and
          ``--boot-disk-size'' can be used to override the boot disk's
          device name and size, respectively.
          +
          By default, ``{default_image}'' is assumed for this flag.
          """.format(
              alias_table=image_utils.GetImageAliasTable(),
              default_image=constants.DEFAULT_IMAGE)

    image = parser.add_argument(
        '--image',
        help='The image that the boot disk will be initialized with.')
    image.detailed_help = AddImageHelp

    parser.add_argument(
        '--can-ip-forward',
        action='store_true',
        help=('If provided, allows the instances to send and receive packets '
              'with non-matching destination or source IP addresses.'))

    parser.add_argument(
        '--description',
        help='Specifies a textual description of the instances.')

    disk = parser.add_argument(
        '--disk',
        action=arg_parsers.AssociativeList(spec={
            'name': str,
            'mode': str,
            'boot': str,
            'device-name': str,
            'auto-delete': str,
        }, append=True),
        help='Attaches persistent disks to the instances.',
        metavar='PROPERTY=VALUE',
        nargs='+')
    disk.detailed_help = """
        Attaches persistent disks to the instances. The disks
        specified must already exist.

        *name*::: The disk to attach to the instances. When creating
        more than one instance and using this property, the only valid
        mode for attaching the disk is read-only (see *mode* below).

        *mode*::: Specifies the mode of the disk. Supported options
        are ``ro'' for read-only and ``rw'' for read-write. If
        omitted, ``rw'' is used as a default. It is an error for mode
        to be ``rw'' when creating more than one instance because
        read-write disks can only be attached to a single instance.

        *boot*::: If ``yes'', indicates that this is a boot disk. The
        virtual machines will use the first partition of the disk for
        their root file systems. The default value for this is ``no''.

        *device-name*::: An optional name that indicates the disk name
        the guest operating system will see. If omitted, a device name
        of the form ``persistent-disk-N'' will be used.

        *auto-delete*::: If ``yes'',  this persistent disk will be
        automatically deleted when the instance is deleted. However,
        if the disk is later detached from the instance, this option
        won't apply. The default value for this is ``no''.
        """

    addresses = parser.add_mutually_exclusive_group()
    addresses.add_argument(
        '--no-address',
        action='store_true',
        help=('If provided, the instances will not be assigned external IP '
              'addresses.'))
    address = addresses.add_argument(
        '--address',
        help='Assigns the given external IP address to an instance.')
    address.detailed_help = """\
        Assigns the given external IP address to an instance. This
        option can only be used when creating a single instance.
        """

    machine_type = parser.add_argument(
        '--machine-type',
        help='Specifies the machine type used for the instances.',
        default=constants.DEFAULT_MACHINE_TYPE)
    machine_type.detailed_help = """\
        Specifies the machine type used for the instances. To get a
        list of available machine types, run 'gcloud compute
        machine-types list'.
        """

    maintenance_policy = parser.add_argument(
        '--maintenance-policy',
        choices=MIGRATION_OPTIONS,
        default='MIGRATE',
        help=('Specifies the behavior of the instances when their host '
              'machines undergo maintenance.'))
    maintenance_policy.detailed_help = """\
        Specifies the behavior of the instances when their host machines undergo
        maintenance. ``TERMINATE'' indicates that the instances should be
        terminated. ``MIGRATE'' indicates that the instances should be
        migrated to a new host. Choosing ``MIGRATE'' will temporarily impact the
        performance of instances during a migration event.
        """

    network = parser.add_argument(
        '--network',
        default=constants.DEFAULT_NETWORK,
        help='Specifies the network that the instances will be part of.')
    network.detailed_help = """\
        Specifies the network that the instances will be part of. If
        omitted, the ``default'' network is used.
        """

    no_restart_on_failure = parser.add_argument(
        '--no-restart-on-failure',
        action='store_true',
        default=False,
        help=('If provided, the instances are not restarted if they are '
              'terminated by Compute Engine.'))
    no_restart_on_failure.detailed_help = """\
        If provided, the instances will not be restarted if they are
        terminated by Compute Engine. By default, failed instances will be
        restarted. This does not affect terminations performed by the user.
    """

    scopes_group = parser.add_mutually_exclusive_group()

    def AddScopesHelp():
      return """\
          Specifies service accounts and scopes for the
          instances. Service accounts generate access tokens that can be
          accessed through the instance metadata server and used to
          authenticate applications on the instance. The account can be
          either an email address or an alias corresponding to a
          service account. If account is omitted, the project's default
          service account is used. The default service account can be
          specified explicitly by using the alias ``default''. Example:

            $ {{command}} my-instance \\
                --scopes compute-rw me@project.gserviceaccount.com=storage-rw
          +
          If this flag is not provided, the ``storage-ro'' scope is
          added to the instances. To create instances with no scopes,
          use ``--no-scopes'':

            $ {{command}} my-instance --no-scopes
          +
          SCOPE can be either the full URI of the scope or an
          alias. Available aliases are:
          +
          [options="header",format="csv",grid="none",frame="none"]
          |========
          Alias,URI
          {aliases}
          |========
          """.format(
              aliases='\n          '.join(
                  ','.join(value) for value in
                  sorted(constants.SCOPES.iteritems())))
    scopes = scopes_group.add_argument(
        '--scopes',
        help='Specifies service accounts and scopes for the instances.',
        metavar='[ACCOUNT=]SCOPE',
        nargs='+')
    scopes.detailed_help = AddScopesHelp

    scopes_group.add_argument(
        '--no-scopes',
        action='store_true',
        help=('If provided, the default scopes ({scopes}) are not added to the '
              'instances.'.format(scopes=', '.join(constants.DEFAULT_SCOPES))))

    tags = parser.add_argument(
        '--tags',
        help='A list of tags to apply to the instances.',
        metavar='TAG',
        nargs='+')
    tags.detailed_help = """\
        Specifies a list of tags to apply to the instances for
        identifying the instances to which network firewall rules will
        apply. See *gcloud-compute-firewalls-create(1)* for more
        details.
        """

    parser.add_argument(
        'names',
        metavar='NAME',
        nargs='+',
        help='The names of the instances to create.')

    parser.add_argument(
        '--zone', required=True,
        help='The zone to create the instances in.')

  @property
  def service(self):
    return self.context['compute'].instances

  @property
  def method(self):
    return 'Insert'

  @property
  def print_resource_type(self):
    return 'instances'

  def ValidateDiskFlags(self, args):
    """Validates the values of all disk-related flags."""
    boot_disk_specified = False

    for disk in args.disk or []:
      disk_name = disk.get('name')
      if not disk_name:
        raise exceptions.ToolException(
            'missing name in --disk; --disk value must be of the form "{0}"'
            .format(DISK_METAVAR))

      mode_value = disk.get('mode')
      if mode_value and mode_value not in ('rw', 'ro'):
        raise exceptions.ToolException(
            'value for mode in --disk must be "rw" or "ro"; received: {0}'
            .format(mode_value))

      # Ensures that the user is not trying to attach a read-write
      # disk to more than one instance.
      if len(args.names) > 1 and mode_value == 'rw':
        raise exceptions.ToolException(
            'cannot attach disk "{0}" in read-write mode to more than one '
            'instance'.format(disk_name))

      boot_value = disk.get('boot')
      if boot_value and boot_value not in ('yes', 'no'):
        raise exceptions.ToolException(
            'value for boot in --disk must be "yes" or "no"; received: {0}'
            .format(boot_value))

      auto_delete_value = disk.get('auto-delete')
      if auto_delete_value and auto_delete_value not in ['yes', 'no']:
        raise exceptions.ToolException(
            'value for auto-delete in --disk must be "yes" or "no"; '
            'received: {0}'
            .format(auto_delete_value))

      # If this is a boot disk and we have already seen a boot disk,
      # we need to fail because only one boot disk can be attached.
      if boot_value == 'yes':
        if boot_disk_specified:
          raise exceptions.ToolException(
              'each instance can have exactly one boot disk; at least two '
              'boot disks were specified through --disk')
        else:
          boot_disk_specified = True

    if args.image and boot_disk_specified:
      raise exceptions.ToolException(
          'each instance can have exactly one boot disk; one boot disk '
          'was specified through --disk and another through --image')

    if not args.image and args.boot_disk_device_name:
      raise exceptions.ToolException(
          '--boot-disk-device-name can only be used in conjunction with the '
          '--image flag')

    if not args.image and args.boot_disk_size:
      raise exceptions.ToolException(
          '--boot-disk-size can only be used in conjunction with the '
          '--image flag')

    if args.boot_disk_size:
      if args.boot_disk_size % constants.BYTES_IN_ONE_GB != 0:
        raise exceptions.ToolException(
            'boot disk size must be a multiple of 1 GB; did you mean "{0}GB"?'
            .format(args.boot_disk_size / constants.BYTES_IN_ONE_GB + 1))

    if not args.image and args.no_boot_disk_auto_delete:
      raise exceptions.ToolException(
          '--no-boot-disk-auto-delete can only be used in conjunction with the '
          '--image flag')

  def UseExistingBootDisk(self, args):
    """Returns True if the user has specified an existing boot disk."""
    return any(disk.get('boot') == 'yes' for disk in args.disk or [])

  def CreateAttachedDiskMessages(self, args):
    """Returns a list of AttachedDisk messages based on command-line args."""
    disks = []

    for disk in args.disk or []:
      name = disk['name']

      # Resolves the mode.
      mode_value = disk.get('mode', 'ro')
      if mode_value == 'rw':
        mode = messages.AttachedDisk.ModeValueValuesEnum.READ_WRITE
      else:
        mode = messages.AttachedDisk.ModeValueValuesEnum.READ_ONLY

      boot = disk.get('boot') == 'yes'
      auto_delete = disk.get('auto-delete') == 'yes'

      disk_uri = self.context['uri-builder'].Build(
          'zones', args.zone, 'disks', name)

      attached_disk = messages.AttachedDisk(
          autoDelete=auto_delete,
          boot=boot,
          deviceName=disk.get('device-name'),
          mode=mode,
          source=disk_uri,
          type=messages.AttachedDisk.TypeValueValuesEnum.PERSISTENT)

      # The boot disk must end up at index 0.
      if boot:
        disks = [attached_disk] + disks
      else:
        disks.append(attached_disk)

    return disks

  def CreateDefaultBootAttachedDiskMessage(self, args):
    """Returns an AttachedDisk message for creating a new boot disk."""
    image_uri = image_utils.ExpandImage(args.image, self.context['uri-builder'])

    if args.boot_disk_size:
      size_gb = args.boot_disk_size / constants.BYTES_IN_ONE_GB
    else:
      size_gb = None

    return messages.AttachedDisk(
        autoDelete=not args.no_boot_disk_auto_delete,
        boot=True,
        deviceName=args.boot_disk_device_name,
        initializeParams=messages.AttachedDiskInitializeParams(
            sourceImage=image_uri,
            diskSizeGb=size_gb),
        mode=messages.AttachedDisk.ModeValueValuesEnum.READ_WRITE,
        type=messages.AttachedDisk.TypeValueValuesEnum.PERSISTENT)

  def CreateServiceAccountMessages(self, args):
    """Returns a list of ServiceAccount messages corresponding to --scopes."""
    if args.no_scopes:
      scopes = []
    else:
      scopes = args.scopes or constants.DEFAULT_SCOPES

    accounts_to_scopes = collections.defaultdict(list)
    for scope in scopes:
      parts = scope.split('=')
      if len(parts) == 1:
        account = 'default'
        scope_uri = scope
      elif len(parts) == 2:
        account, scope_uri = parts
      else:
        raise exceptions.ToolException(
            '--scopes values must be of the form [ACCOUNT=]SCOPE; received: {0}'
            .format(scope))

      # Expands the scope if the user provided an alias like
      # "compute-rw".
      scope_uri = constants.SCOPES.get(scope_uri, scope_uri)

      accounts_to_scopes[account].append(scope_uri)

    res = []
    for account, scopes in sorted(accounts_to_scopes.iteritems()):
      res.append(messages.ServiceAccount(
          email=account,
          scopes=sorted(scopes)))
    return res

  def CreateNetworkInterfaceMessage(self, args):
    """Returns a new NetworkInterface message."""
    network_uri = self.context['uri-builder'].Build(
        'global', 'networks', args.network)
    network_interface = messages.NetworkInterface(
        network=network_uri)

    if not args.no_address:
      access_config = messages.AccessConfig(
          name=constants.DEFAULT_ACCESS_CONFIG_NAME,
          type=messages.AccessConfig.TypeValueValuesEnum.ONE_TO_ONE_NAT)

      # If the user provided an external IP, populate the access
      # config with it.
      if args.address:
        access_config.natIP = args.address

      network_interface.accessConfigs = [access_config]

    return network_interface

  def CreateRequests(self, args):
    self.ValidateDiskFlags(args)

    machine_type_uri = self.context['uri-builder'].Build(
        'zones', args.zone, 'machineTypes', args.machine_type)

    metadata = metadata_utils.ConstructMetadataMessage(
        metadata=args.metadata, metadata_from_file=args.metadata_from_file)

    network_interface = self.CreateNetworkInterfaceMessage(args)

    scheduling = messages.Scheduling(
        automaticRestart=not args.no_restart_on_failure,
        onHostMaintenance=(
            messages.Scheduling.OnHostMaintenanceValueValuesEnum(
                args.maintenance_policy)))

    service_accounts = self.CreateServiceAccountMessages(args)

    if args.tags:
      tags = messages.Tags(items=args.tags)
    else:
      tags = None


    disks = self.CreateAttachedDiskMessages(args)

    if not self.UseExistingBootDisk(args):
      disks = [self.CreateDefaultBootAttachedDiskMessage(args)] + disks

    requests = []
    for name in args.names:
      requests.append(messages.ComputeInstancesInsertRequest(
          instance=messages.Instance(
              canIpForward=args.can_ip_forward,
              disks=disks,
              description=args.description,
              machineType=machine_type_uri,
              metadata=metadata,
              name=name,
              networkInterfaces=[network_interface],
              serviceAccounts=service_accounts,
              scheduling=scheduling,
              tags=tags,
          ),
          project=self.context['project'],
          zone=args.zone))

    return requests


CreateInstances.detailed_help = {
    'brief': 'Create Compute Engine virtual machine instances',
    'DESCRIPTION': """\
        *{command}* facilitates the creation of Google Compute Engine
        virtual machines. For example, running:

          $ {command} \\
              my-instance-1 my-instance-2 my-instance-3 \\
              --zone us-central1-a

        will create three instances called ``my-instance-1'',
        ``my-instance-2'', and ``my-instance-3'' in the
        ``us-central1-a'' zone.

        For more examples, refer to the *EXAMPLES* section below.
        """,
    'EXAMPLES': """\
        To create an instance with the latest ``Red Hat Enterprise Linux
        6'' image available, run:

          $ {command} my-instance \\
              --image rhel-6 --zone us-central1-a
        """,
}
