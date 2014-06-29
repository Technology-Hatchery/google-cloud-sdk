# Copyright 2014 Google Inc. All Rights Reserved.

"""Implements the command for copying files from and to virtual machines."""
import collections
import getpass
import logging
import subprocess

from googlecloudsdk.calliope import exceptions
from googlecloudsdk.compute.lib import ssh_utils


RemoteFile = collections.namedtuple(
    'RemoteFile', ['user', 'instance_name', 'file_path'])
LocalFile = collections.namedtuple(
    'LocalFile', ['file_path'])


class CopyFiles(ssh_utils.BaseSSHCommand):
  """Copy files to and from Google Compute Engine virtual machines."""

  @staticmethod
  def Args(parser):
    ssh_utils.BaseSSHCommand.Args(parser)

    parser.add_argument(
        '--zone',
        help='The zone of the instance.',
        required=True)

    parser.add_argument(
        'sources',
        help='Specifies a source file.',
        metavar='[[USER@]INSTANCE:]SRC',
        nargs='+')

    parser.add_argument(
        'destination',
        help='Specifies a destination for the source files.',
        metavar='[[USER@]INSTANCE:]DEST')

  def Run(self, args):
    super(CopyFiles, self).Run(args)

    file_specs = []

    # Parses the positional arguments.
    for arg in args.sources + [args.destination]:
      # If the argument begins with "./" or "/", then we are dealing
      # with a local file that can potentially contain colons, so we
      # avoid splitting on colons. The case of remote files containing
      # colons is handled below by splitting only on the first colon.
      if arg.startswith('./') or arg.startswith('/'):
        file_specs.append(LocalFile(arg))
        continue

      host_file_parts = arg.split(':', 1)
      if len(host_file_parts) == 1:
        file_specs.append(LocalFile(host_file_parts[0]))
      else:
        user_host, file_path = host_file_parts
        user_host_parts = user_host.split('@', 1)
        if len(user_host_parts) == 1:
          user = getpass.getuser()
          instance = user_host_parts[0]
        else:
          user, instance = user_host_parts

        file_specs.append(RemoteFile(user, instance, file_path))

    logging.debug('Normalized arguments: %s', file_specs)

    # Validates the positional arguments.
    sources = file_specs[:-1]
    destination = file_specs[-1]
    if isinstance(destination, LocalFile):
      for source in sources:
        if isinstance(source, LocalFile):
          raise exceptions.ToolException(
              'all sources must be remote files when the destination '
              'is local')

    else:  # RemoteFile
      for source in sources:
        if isinstance(source, RemoteFile):
          raise exceptions.ToolException(
              'all sources must be local files when the destination '
              'is remote')

    instances = set()
    for file_spec in file_specs:
      if isinstance(file_spec, RemoteFile):
        instances.add(file_spec.instance_name)

    if len(instances) > 1:
      raise exceptions.ToolException(
          'copies must involve exactly one virtual machine instance; '
          'your invocation refers to {0} instances: {1}'.format(
              len(instances), ', '.join(sorted(instances))))

    self.EnsureSSHKeyIsInProject(user)

    instance_resource = self.GetInstance(instances.pop(), args.zone)
    external_ip_address = ssh_utils.GetExternalIPAddress(instance_resource)

    self.WaitUntilSSHable(user, external_ip_address)

    # Builds the scp command.
    scp_args = [
        self.scp_executable,
        '-i', self.ssh_key_file,
        '-r',
    ]
    for file_spec in file_specs:
      if isinstance(file_spec, LocalFile):
        scp_args.append(file_spec.file_path)

      else:
        scp_args.append('{0}:{1}'.format(
            ssh_utils.UserHost(file_spec.user, external_ip_address),
            file_spec.file_path))

    logging.debug('scp command: %s', ' '.join(scp_args))
    try:
      subprocess.check_call(scp_args)
    except OSError as e:
      raise exceptions.ToolException(
          '{0}: {1}'.format(e.strerror, ' '.join(scp_args)))
    except subprocess.CalledProcessError as e:
      raise exceptions.ToolException(
          'exit code {0}: {1}'.format(e.returncode, ' '.join(scp_args)))


CopyFiles.detailed_help = {
    'brief': 'Copy files to and from Google Compute Engine virtual machines',
    'DESCRIPTION': """\
        *{command}* copies files between a virtual machine instance
        and your local machine.

        To denote a remote file, prefix the file name with the virtual
        machine instance's name (e.g., ``my-instance:~/my-file''). To
        denote a local file, do not add a prefix to the file name
        (e.g., ``~/my-file''). For example, to copy a remote directory
        to your local host, run:

          $ {command} \\
              my-instance:~/remote-dir \\
              ~/local-dir \\
              --zone us-central2-a

        In the above example, ``~/remote-dir'' from
        ``my-instance'' is copied into the ``~/local-dir''
        directory.

        Conversely, files from your local computer can be copied to a
        virtual machine:

          $ {command} \\
              ~/my-local-file-1 \\
              ~/my-local-file-2 \\
              my-instance:~/remote-destination \\
              --zone us-central2-a

        If a file contains a colon (``:''), you must specify it by
        either using an absolute path or a path that begins with
        ``./''.

        Under the covers, *scp(1)* is used to facilitate the transfer.

        When the destination is local, all sources must be the same
        virtual machine instance. When the destination is remote, all
        source must be local.
        """,
}
