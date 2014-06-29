# Copyright 2014 Google Inc. All Rights Reserved.
"""Command for reading the serial port output of an instance."""
from googlecloudapis.compute.v1 import compute_v1_messages as messages
from googlecloudsdk.calliope import base
from googlecloudsdk.compute.lib import request_helper
from googlecloudsdk.core import log


class GetSerialPortOutput(base.Command):
  """Read output from a virtual machine instance's serial port."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--zone',
        help='Specifies the zone of the instance.',
        required=True)
    parser.add_argument(
        'name',
        help='The name of the instance.')

  def Run(self, args):
    request = (self.context['compute'].instances,
               'GetSerialPortOutput',
               messages.ComputeInstancesGetSerialPortOutputRequest(
                   instance=args.name,
                   project=self.context['project'],
                   zone=args.zone))

    objects = list(request_helper.MakeRequests(
        requests=[request],
        http=self.context['http'],
        batch_url=self.context['batch-url'],
        custom_get_requests=None))
    return objects[0].contents

  def Display(self, _, response):
    log.out.write(response)


GetSerialPortOutput.detailed_help = {
    'brief': "Read output from a virtual machine instance's serial port",
    'DESCRIPTION': """\
        {command} is used to get the output from a Google Compute
        Engine virtual machine's serial port. The serial port output
        from the virtual machine will be printed to standard out. This
        information can be useful for diagnostic purposes.
        """,
}
