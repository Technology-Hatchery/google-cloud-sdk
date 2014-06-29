# Copyright 2013 Google Inc. All Rights Reserved.

"""This file can be executed directly to run the CLI or loaded as a module.
"""
import os

from googlecloudsdk.core import cli

_cli = cli.CLILoader(
    name='sql',
    command_root_directory=os.path.join(
        cli.GoogleCloudSDKPackageRoot(),
        'sql',
        'tools')).Generate()

sql = _cli.EntryPoint()


def main():
  _cli.Execute()

if __name__ == '__main__':
  main()
