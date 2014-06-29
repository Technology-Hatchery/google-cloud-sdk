# Copyright 2013 Google Inc. All Rights Reserved.

"""The super-group for the update manager."""

import argparse
import os

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import config
from googlecloudsdk.core import log
from googlecloudsdk.core.updater import update_manager
from googlecloudsdk.core.util import platforms


class Components(base.Group):
  """Install, update, or remove the tools in the Google Cloud SDK."""

  @staticmethod
  def Args(parser):
    """Sets args for gcloud components."""
    # An override for the location to install components into.
    parser.add_argument('--sdk-root-override', required=False,
                        help=argparse.SUPPRESS)
    # A different URL to look at instead of the default.
    parser.add_argument('--snapshot-url-override', required=False,
                        help=argparse.SUPPRESS)
    # This is not a commonly used option.  You can use this flag to create a
    # Cloud SDK install for an OS other than the one you are running on.
    # Running the updater multiple times for different operating systems could
    # result in an inconsistent install.
    parser.add_argument('--operating-system-override', required=False,
                        help=argparse.SUPPRESS)
    # This is not a commonly used option.  You can use this flag to create a
    # Cloud SDK install for a processor architecture other than that of your
    # current machine.  Running the updater multiple times for different
    # architectures could result in an inconsistent install.
    parser.add_argument('--architecture-override', required=False,
                        help=argparse.SUPPRESS)

  # pylint:disable=g-missing-docstring
  @exceptions.RaiseToolExceptionInsteadOf(platforms.InvalidEnumValue)
  def Filter(self, tool_context, args):

    if config.INSTALLATION_CONFIG.IsAlternateReleaseChannel():
      log.warning('You are using alternate release channel: [%s]',
                  config.INSTALLATION_CONFIG.release_channel)
      # Always show the URL if using a non standard release channel.
      log.warning('Snapshot URL for this release channel is: [%s]',
                  config.INSTALLATION_CONFIG.snapshot_url)

    os_override = platforms.OperatingSystem.FromId(
        args.operating_system_override)
    arch_override = platforms.Architecture.FromId(args.architecture_override)

    platform = platforms.Platform.Current(os_override, arch_override)
    root = (os.path.expanduser(args.sdk_root_override)
            if args.sdk_root_override else None)
    url = (os.path.expanduser(args.snapshot_url_override)
           if args.snapshot_url_override else None)

    self.update_manager = update_manager.UpdateManager(
        sdk_root=root, url=url, platform_filter=platform,
        out_stream=log.out)
