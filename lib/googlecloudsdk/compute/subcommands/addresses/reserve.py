# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for reserving IP addresses."""
from googlecloudapis.compute.v1 import compute_v1_messages as messages
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.compute.lib import base_classes
from googlecloudsdk.compute.lib import name_generator


class Reserve(base_classes.BaseAsyncMutator):
  """Reserve IP addresses."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--region',
        help='The region of the addresses.',
        required=True)

    addresses = parser.add_argument(
        '--addresses',
        metavar='ADDRESS',
        nargs='+',
        help='Ephemeral IP addresses to promote to reserved status.')
    addresses.detailed_help = """\
        Ephemeral IP addresses to promote to reserved status. Only addresses
        that are being used by resources in the project can be promoted. When
        providing this flag, a parallel list of names for the addresses can
        be provided. For example,

          $ {command} my-address-1 my-address-2 \\
              --addresses 162.222.181.197 162.222.181.198 \\
              --region us-central2

        will result in 162.222.181.197 being reserved as
        ``my-address-1'' and 162.222.181.198 as ``my-address-2''. If
        no names are given, randomly-generated names will be assigned
        to the IP addresses.
        """

    parser.add_argument(
        '--description',
        help='An optional textual description for the addresses.')

    parser.add_argument(
        'name',
        metavar='NAME',
        nargs='*',
        help='The names to assign to the reserved IP addresses.')

  @property
  def service(self):
    return self.context['compute'].addresses

  @property
  def method(self):
    return 'Insert'

  @property
  def print_resource_type(self):
    return 'addresses'

  def CreateRequests(self, args):
    if args.addresses:
      addresses = args.addresses

      if args.name:
        if len(args.addresses) == len(args.name):
          names = args.name
        else:
          raise exceptions.ToolException(
              'you must provide the same number of names as addresses provided '
              'through --addresses')

      # No names were provided, so we have to generate random names.
      else:
        names = [name_generator.GenerateRandomName() for _ in args.addresses]

    elif args.name:
      names = args.name
      addresses = [None] * len(names)
    else:
      raise exceptions.ToolException('at least one name must be provided')

    requests = []
    for address, name in zip(addresses, names):
      request = messages.ComputeAddressesInsertRequest(
          address=messages.Address(
              address=address,
              description=args.description,
              name=name,
          ),
          project=self.context['project'],
          region=args.region)
      requests.append(request)

    return requests


Reserve.detailed_help = {
    'brief': 'Reserve IP addresses',
    'DESCRIPTION': """\
        *{command}* is used to reserve one or more IP addresses. Once
        an IP address is reserved, it will be associated with the
        project until it is released using 'gcloud compute addresses
        release'. Ephemeral IP addresses that are in use by resources
        in the project, can be reserved using the ``--addresses''
        flag.
        """,
    'EXAMPLES': """\
        To reserve three IP addresses in the ``us-central2'' region,
        run:

          $ {command} my-address-1 my-address-2 my-address-3 \\
              --region us-central2

        To reserve ephemeral IP addresses 162.222.181.198 and
        23.251.146.189 which are being used by virtual machine
        instances in the ``us-central2'' region, run:

          $ {command} --addresses 162.222.181.198 23.251.146.189 \\
              --region us-central2

        In the above invocation, the two addresses will be assigned
        random names.
        """,
}
