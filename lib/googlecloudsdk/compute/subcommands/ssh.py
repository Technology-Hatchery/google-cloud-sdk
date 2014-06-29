# Copyright 2014 Google Inc. All Rights Reserved.

"""Implements the command for SSHing into an instance."""
import getpass
import logging
import subprocess

from googlecloudsdk.calliope import exceptions
from googlecloudsdk.compute.lib import ssh_utils


class SSH(ssh_utils.BaseSSHCommand):
  """SSH into a virtual machine instance."""

  @staticmethod
  def Args(parser):
    ssh_utils.BaseSSHCommand.Args(parser)

    user_host = parser.add_argument(
        'user_host',
        help='Specifies the instance to SSH into.',
        metavar='[USER@]INSTANCE')
    user_host.detailed_help = """\
        Specifies the instance to SSH into. If ``INSTANCE'' is the
        name of the instance, the ``--zone'' flag must be
        specified. If ``INSTANCE'' is a suffix of the instance's URI
        that contains the zone (e.g.,
        ``us-central2-a/instances/my-instance''), then ``--zone'' can
        be omitted.
        +
        ``USER'' specifies the username with which to SSH. If omitted,
        $USER from the environment is selected.
        """

    parser.add_argument(
        '--command',
        help='A command to run on the virtual machine.')

    parser.add_argument(
        '--tty', '-t',
        action='store_true',
        help="""\
            If provided, allocates a pseudo-tty. This is useful if a command
            is provided which requires interaction from the user (e.g.,
            ``--command /bin/bash''). This is equivalent to ``-t'' in
            *ssh(1)*.
            """)

    parser.add_argument(
        '--zone',
        help='The zone of the instance.',
        required=True)

    parser.add_argument(
        '--container',
        help="""\
            The name of a container inside of the virtual machine instance to
            connect to. This only applies to virtual machines that are using
            a Google container virtual machine image. For more information,
            see link:https://developers.google.com/compute/docs/containers[].
            """)

  def Run(self, args):
    super(SSH, self).Run(args)
    parts = args.user_host.split('@')
    if len(parts) == 1:
      user = getpass.getuser()
      instance = parts[0]
    elif len(parts) == 2:
      user, instance = parts
    else:
      raise exceptions.ToolException(
          'expected argument of the form [USER@]INSTANCE; received: {0}'
          .format(args.user_host))

    self.EnsureSSHKeyIsInProject(user)

    instance_resource = self.GetInstance(instance, args.zone)
    external_ip_address = ssh_utils.GetExternalIPAddress(instance_resource)

    self.WaitUntilSSHable(user, external_ip_address)

    ssh_args = [
        self.ssh_executable,
        '-i',
        self.ssh_key_file,
    ]
    # Allocates a tty if one was explicitly requested, or no command was
    # provided and a container was provided.
    if args.tty or (args.container and not args.command):
      ssh_args.append('-t')
    ssh_args.append(ssh_utils.UserHost(user, external_ip_address))

    if args.container:
      ssh_args.append('--')
      ssh_args.append('container_exec')
      ssh_args.append(args.container)
      # Runs the given command inside the given container if --command was
      # specified, otherwise runs /bin/sh.
      if args.command:
        ssh_args.append(args.command)
      else:
        ssh_args.append('/bin/sh')

    elif args.command:
      ssh_args.append('--')
      ssh_args.append(args.command)

    logging.debug('running ssh command: %s', ' '.join(ssh_args))
    try:
      subprocess.check_call(ssh_args)
    except OSError as e:
      raise exceptions.ToolException(
          '{0}: {1}'.format(e.strerror, ' '.join(ssh_args)))
    except subprocess.CalledProcessError as e:
      raise exceptions.ToolException(
          'exit code {0}: {1}'.format(e.returncode, ' '.join(ssh_args)))


SSH.detailed_help = {
    'brief': 'SSH into a virtual machine instance',
    'DESCRIPTION': """\
        *{command}* is a thin wrapper around the 'ssh' command that
        takes care of authentication and the translation of the
        instance name into an IP address.

        This command ensures that the user's public SSH key is present
        in the project's metadata. If the user does not have a public
        SSH key, one is generated using 'ssh-keygen'.
        """,
    'EXAMPLES': """\
        To SSH into ``my-instance'' in zone ``us-central2-a'', run:

          $ {command} my-instance --zone us-central2-a

        You can omit the ``--zone'' flag if the zone is provided in
        the positional argument:

          $ {command} us-central2-a/instances/my-instance

        You can also run a command on the virtual machine. For
        example, to get a snapshot of the guest's process tree, run:

          $ {command} my-instance --zone us-central2-a --command "ps -ejH"

        If you are using the Google container virtual machine image, you
        can ssh into one of your containers with:

          $ {command} my-instance \\
              --zone us-central2-a \\
              --container my-container
        """,
}
