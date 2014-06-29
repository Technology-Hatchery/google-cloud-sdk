#!/usr/bin/env python
# coding=utf8
# Copyright 2013 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Main module for Google Cloud Storage command line tool."""

import ConfigParser
import errno
import getopt
import logging
import os
import pkgutil
import re
import signal
import socket
import sys
import tempfile
import textwrap
import traceback

# Load the gsutil version number and append it to boto.UserAgent so the value is
# set before anything instantiates boto. This has to run after THIRD_PARTY_DIR
# is modified (done in gsutil.py) but before any calls are made that would cause
# boto.s3.Connection to be loaded - otherwise the Connection class would end up
# with a static reference to the pre-modified version of the UserAgent field,
# so boto requests would not include gsutil/version# in the UserAgent string.
import boto
import gslib
boto.UserAgent += ' gsutil/%s (%s)' % (gslib.VERSION, sys.platform)
boto.UserAgent += ' Cloud SDK Command Line Tool'

import apiclient.discovery
import boto.exception
from gslib import util
from gslib import GSUTIL_DIR
from gslib import wildcard_iterator
from gslib.command_runner import CommandRunner
from gslib.exception import CommandException
from gslib.util import BOTO_IS_SECURE
from gslib.util import GetBotoConfigFileList
from gslib.util import GetConfigFilePath
from gslib.util import HasConfiguredCredentials
from gslib.util import IsRunningInteractively
import gslib.exception
import httplib2
import oauth2client

# We don't use the oauth2 authentication plugin directly; importing it here
# ensures that it's loaded and available by default when an operation requiring
# authentication is performed.
try:
  from gslib.third_party.oauth2_plugin import oauth2_plugin
except ImportError:
  pass

DEBUG_WARNING = """
***************************** WARNING *****************************
*** You are running gsutil with debug output enabled.
*** Be aware that debug output includes authentication credentials.
*** Make sure to remove the value of the Authorization header for
*** each HTTP request printed to the console prior to posting to
*** a public medium such as a forum post or Stack Overflow.
***************************** WARNING *****************************
""".lstrip()

HTTP_WARNING = """
***************************** WARNING *****************************
*** You are running gsutil with either the boto config variable "is_secure" set
*** to False or the "https_validate_certificates" config variable set to False.
*** These options should always be set to True in production environments, to
*** protect against intercepted bearer tokens, man-in-the-middle attacks, and
*** leaking of user data.
***************************** WARNING *****************************
""".lstrip()

debug = 0

# Temp files to delete, if possible, when program exits.
cleanup_files = []


def _Cleanup():
  for fname in cleanup_files:
    try:
      os.remove(fname)
    except OSError:
      pass


def _OutputAndExit(message):
  if debug == 4:
    stack_trace = traceback.format_exc()
    err = ('DEBUG: Exception stack trace:\n    %s\n' %
           re.sub('\\n', '\n    ', stack_trace))
  else:
    err = '%s\n' % message
  sys.stderr.write(err.encode('utf-8'))
  sys.exit(1)


def _OutputUsageAndExit(command_runner):
  command_runner.RunNamedCommand('help')
  sys.exit(1)


def _ConfigureLogging(level=logging.INFO):
  """Similar to logging.basicConfig() except it always adds a handler."""
  handler = logging.StreamHandler()
  root_logger = logging.getLogger()
  root_logger.addHandler(handler)
  root_logger.setLevel(level)


def main():
  # These modules must be imported after importing gslib.__main__.
  import gslib.command
  import gslib.util
  from gslib.third_party.oauth2_plugin import oauth2_client
  from gslib.util import MultiprocessingIsAvailable
  if MultiprocessingIsAvailable()[0]:
    # These setup methods must be called, and, on Windows, they can only be
    # called from within an "if __name__ == '__main__':" block.
    gslib.util.InitializeMultiprocessingVariables()
    gslib.command.InitializeMultiprocessingVariables()
  oauth2_client.InitializeMultiprocessingVariables()

  global debug

  if not (2, 6) <= sys.version_info[:3] < (3,):
    raise gslib.exception.CommandException(
        'gsutil requires python 2.6 or 2.7.')

  config_file_list = GetBotoConfigFileList()
  command_runner = CommandRunner(config_file_list)
  headers = {}
  parallel_operations = False
  quiet = False
  version = False
  debug = 0

  # If user enters no commands just print the usage info.
  if len(sys.argv) == 1:
    sys.argv.append('help')

  # Change the default of the 'https_validate_certificates' boto option to
  # True (it is currently False in boto).
  if not boto.config.has_option('Boto', 'https_validate_certificates'):
    if not boto.config.has_section('Boto'):
      boto.config.add_section('Boto')
    boto.config.setbool('Boto', 'https_validate_certificates', True)

  # If ca_certificates_file is configured use it; otherwise configure boto to
  # use the cert roots distributed with gsutil.
  if not boto.config.get_value('Boto', 'ca_certificates_file', None):
    disk_certs_file = os.path.abspath(
        os.path.join(gslib.GSLIB_DIR, 'data', 'cacerts.txt'))
    if not os.path.exists(disk_certs_file):
      # If the file is not present on disk, this means the gslib module doesn't
      # actually exist on disk anywhere. This can happen if it's being imported
      # from a zip file. Unfortunately, we have to copy the certs file to a
      # local temp file on disk because the underlying SSL socket requires it
      # to be a filesystem path.
      certs_data = pkgutil.get_data('gslib', 'data/cacerts.txt')
      if not certs_data:
        raise gslib.exception.CommandException(
            'Certificates file not found. Please reinstall gsutil from scratch')
      fd, fname = tempfile.mkstemp(suffix='.txt', prefix='gsutil-cacerts')
      f = os.fdopen(fd, 'w')
      f.write(certs_data)
      f.close()
      disk_certs_file = fname
      cleanup_files.append(disk_certs_file)
    boto.config.set('Boto', 'ca_certificates_file', disk_certs_file)

  try:
    try:
      opts, args = getopt.getopt(sys.argv[1:], 'dDvo:h:mq',
                                 ['debug', 'detailedDebug', 'version', 'option',
                                  'help', 'header', 'multithreaded', 'quiet'])
    except getopt.GetoptError as e:
      _HandleCommandException(gslib.exception.CommandException(e.msg))
    for o, a in opts:
      if o in ('-d', '--debug'):
        # Passing debug=2 causes boto to include httplib header output.
        debug = 2
      elif o in ('-D', '--detailedDebug'):
        # We use debug level 3 to ask gsutil code to output more detailed
        # debug output. This is a bit of a hack since it overloads the same
        # flag that was originally implemented for boto use. And we use -DD
        # to ask for really detailed debugging (i.e., including HTTP payload).
        if debug == 3:
          debug = 4
        else:
          debug = 3
      elif o in ('-?', '--help'):
        _OutputUsageAndExit(command_runner)
      elif o in ('-h', '--header'):
        (hdr_name, _, hdr_val) = a.partition(':')
        if not hdr_name:
          _OutputUsageAndExit(command_runner)
        headers[hdr_name.lower()] = hdr_val
      elif o in ('-m', '--multithreaded'):
        parallel_operations = True
      elif o in ('-q', '--quiet'):
        quiet = True
      elif o in ('-v', '--version'):
        version = True
      elif o in ('-o', '--option'):
        (opt_section_name, _, opt_value) = a.partition('=')
        if not opt_section_name:
          _OutputUsageAndExit(command_runner)
        (opt_section, _, opt_name) = opt_section_name.partition(':')
        if not opt_section or not opt_name:
          _OutputUsageAndExit(command_runner)
        if not boto.config.has_section(opt_section):
          boto.config.add_section(opt_section)
        boto.config.set(opt_section, opt_name, opt_value)
    httplib2.debuglevel = debug
    if debug > 1:
      sys.stderr.write(DEBUG_WARNING)
    if debug == 2:
      _ConfigureLogging(level=logging.DEBUG)
    elif debug > 2:
      _ConfigureLogging(level=logging.DEBUG)
      command_runner.RunNamedCommand('ver', ['-l'])
      config_items = []
      try:
        config_items.extend(boto.config.items('Boto'))
        config_items.extend(boto.config.items('GSUtil'))
      except ConfigParser.NoSectionError:
        pass
      sys.stderr.write('config_file_list: %s\n' % config_file_list)
      sys.stderr.write('config: %s\n' % str(config_items))
    elif quiet:
      _ConfigureLogging(level=logging.WARNING)
    else:
      _ConfigureLogging(level=logging.INFO)
      # apiclient and oauth2client use info logging in places that would better
      # correspond to gsutil's debug logging (e.g., when refreshing access
      # tokens).
      oauth2client.client.logger.setLevel(logging.WARNING)
      apiclient.discovery.logger.setLevel(logging.WARNING)

    is_secure = BOTO_IS_SECURE
    if not is_secure[0]:
      sys.stderr.write(HTTP_WARNING)

    if version:
      command_name = 'version'
    elif not args:
      command_name = 'help'
    else:
      command_name = args[0]

    # Unset http_proxy environment variable if it's set, because it confuses
    # boto. (Proxies should instead be configured via the boto config file.)
    if 'http_proxy' in os.environ:
      if debug > 1:
        sys.stderr.write(
            'Unsetting http_proxy environment variable within gsutil run.\n')
      del os.environ['http_proxy']

    return _RunNamedCommandAndHandleExceptions(
        command_runner, command_name, args[1:], headers, debug,
        parallel_operations)
  finally:
    _Cleanup()


def _HandleUnknownFailure(e):
  # Called if we fall through all known/handled exceptions. Allows us to
  # print a stacktrace if -D option used.
  if debug > 2:
    stack_trace = traceback.format_exc()
    sys.stderr.write('DEBUG: Exception stack trace:\n    %s\n' %
                     re.sub('\\n', '\n    ', stack_trace))
  else:
    _OutputAndExit('Failure: %s.' % e)


def _HandleCommandException(e):
  if e.informational:
    _OutputAndExit(e.reason)
  else:
    _OutputAndExit('CommandException: %s' % e.reason)


def _HandleControlC(signal_num, cur_stack_frame):
  """Called when user hits ^C so we can print a brief message instead of
  the normal Python stack trace (unless -D option is used)."""
  if debug > 2:
    stack_trace = ''.join(traceback.format_list(traceback.extract_stack()))
    _OutputAndExit(
        'DEBUG: Caught signal %d - Exception stack trace:\n'
        '    %s' % (signal_num, re.sub('\\n', '\n    ', stack_trace)))
  else:
    _OutputAndExit('Caught signal %d - exiting' % signal_num)


def _HandleSigQuit(signal_num, cur_stack_frame):
  """Called when user hits ^\\, so we can force breakpoint a running gsutil."""
  import pdb
  pdb.set_trace()

def _ConstructAclHelp(default_project_id):
  acct_help_part_1 = (
"""Your request resulted in an AccountProblem (403) error. Usually this happens
if you attempt to create a bucket or upload an object without having first
enabled billing for the project you are using. To remedy this problem, please do
the following:

1. Navigate to the https://cloud.google.com/console#/project, click on the
   project you will use, and then copy the Project Number listed under that
   project.

""")
  acct_help_part_2 = '\n'
  if default_project_id:
    acct_help_part_2 = (
"""2. Click "Google Cloud Storage" on the left hand pane, and then check that
the value listed for "x-goog-project-id" on this page matches the project ID
(%s) from your boto config file.

""" % default_project_id)
  acct_help_part_3 = (
"""Check whether there's an "!" next to Billing. If so, click Billing and then
enable billing for this project. Note that it can take up to one hour after
enabling billing for the project to become activated for creating buckets and
uploading objects.

If the above doesn't resolve your AccountProblem, please send mail to
gs-team@google.com requesting assistance, noting the exact command you ran, the
fact that you received a 403 AccountProblem error, and your project ID. Please
do not post your project ID on StackOverflow.

Note: It's possible to use Google Cloud Storage without enabling billing if
you're only listing or reading objects for which you're authorized, or if
you're uploading objects to a bucket billed to a project that has billing
enabled. But if you're attempting to create buckets or upload objects to a
bucket owned by your own project, you must first enable billing for that
project.""")
  return (acct_help_part_1, acct_help_part_2, acct_help_part_3)

def _RunNamedCommandAndHandleExceptions(command_runner, command_name, args=None,
                                        headers=None, debug=0,
                                        parallel_operations=False):
  try:
    # Catch ^C so we can print a brief message instead of the normal Python
    # stack trace.
    signal.signal(signal.SIGINT, _HandleControlC)
    # Catch ^\ so we can force a breakpoint in a running gsutil.
    if not util.IS_WINDOWS:
      signal.signal(signal.SIGQUIT, _HandleSigQuit)
    return command_runner.RunNamedCommand(command_name, args, headers, debug,
                                          parallel_operations)
  except AttributeError as e:
    if str(e).find('secret_access_key') != -1:
      _OutputAndExit('Missing credentials for the given URI(s). Does your '
                     'boto config file contain all needed credentials?')
    else:
      _OutputAndExit(str(e))
  except boto.exception.StorageDataError as e:
    _OutputAndExit('StorageDataError: %s.' % e.reason)
  except boto.exception.BotoClientError as e:
    _OutputAndExit('BotoClientError: %s.' % e.reason)
  except gslib.exception.CommandException as e:
    _HandleCommandException(e)
  except getopt.GetoptError as e:
    _HandleCommandException(gslib.exception.CommandException(e.msg))
  except boto.exception.InvalidAclError as e:
    _OutputAndExit('InvalidAclError: %s.' % str(e))
  except boto.exception.InvalidUriError as e:
    _OutputAndExit('InvalidUriError: %s.' % e.message)
  except gslib.exception.ProjectIdException as e:
    _OutputAndExit('ProjectIdException: %s.' % e.reason)
  except boto.auth_handler.NotReadyToAuthenticate:
    _OutputAndExit('NotReadyToAuthenticate')
  except OSError as e:
    _OutputAndExit('OSError: %s.' % e.strerror)
  except IOError as e:
    if e.errno == errno.EPIPE and not IsRunningInteractively():
      # If we get a pipe error, this just means that the pipe to stdout or
      # stderr is broken. This can happen if the user pipes gsutil to a command
      # that doesn't use the entire output stream. Instead of raising an error,
      # just swallow it up and exit cleanly.
      sys.exit(0)
    else:
      raise
  except wildcard_iterator.WildcardException as e:
    _OutputAndExit(e.reason)
  except boto.exception.StorageResponseError as e:
    # Check for access denied, and provide detail to users who have no boto
    # config file (who might previously have been using gsutil only for
    # accessing publicly readable buckets and objects).
    if (e.status == 403
        or (e.status == 400 and e.code == 'MissingSecurityHeader')):
      _, _, detail = util.ParseErrorDetail(e)
      if detail and detail.find('x-goog-project-id header is required') != -1:
        _OutputAndExit('\n'.join(textwrap.wrap(
            'You are attempting to perform an operation that requires an '
            'x-goog-project-id header, with none configured. Please re-run '
            'gsutil config and make sure to follow the instructions for '
            'finding and entering your default project id.')))
      if (not HasConfiguredCredentials() and
          not boto.config.get_value('Tests', 'bypass_anonymous_access_warning',
                                    False)):
        # The check above allows tests to assert that we get a particular,
        # expected failure, rather than always encountering this error message
        # when there are no configured credentials. This allows tests to
        # simulate a second user without permissions, without actually requiring
        # two separate configured users.
        _OutputAndExit('\n'.join(textwrap.wrap(
            'You are attempting to access protected data with no configured '
            'credentials. Please visit '
            'https://cloud.google.com/console#/project and sign up for an '
            'account, and then run the "gsutil config" command to configure '
            'gsutil to use these credentials.')))
      elif (e.error_code == 'AccountProblem'
            and ','.join(args).find('gs://') != -1):
        default_project_id = boto.config.get_value('GSUtil',
                                                   'default_project_id')
        (acct_help_part_1, acct_help_part_2, acct_help_part_3) = (
            _ConstructAclHelp(default_project_id))
        if default_project_id:
          _OutputAndExit(acct_help_part_1 + acct_help_part_2 + '3. ' +
                         acct_help_part_3)
        else:
          _OutputAndExit(acct_help_part_1 + '2. ' + acct_help_part_3)

    exc_name, message, detail = util.ParseErrorDetail(e)
    _OutputAndExit(util.FormatErrorMessage(
        exc_name, e.status, e.code, e.reason, message, detail))
  except boto.exception.ResumableUploadException as e:
    _OutputAndExit('ResumableUploadException: %s.' % e.message)
  except socket.error as e:
    if e.args[0] == errno.EPIPE:
      # Retrying with a smaller file (per suggestion below) works because
      # the library code send loop (in boto/s3/key.py) can get through the
      # entire file and then request the HTTP response before the socket
      # gets closed and the response lost.
      message = (
"""
Got a "Broken pipe" error. This can happen to clients using Python 2.x,
when the server sends an error response and then closes the socket (see
http://bugs.python.org/issue5542). If you are trying to upload a large
object you might retry with a small (say 200k) object, and see if you get
a more specific error code.
""")
      _OutputAndExit(message)
    else:
      _HandleUnknownFailure(e)
  except Exception as e:
    # Check for two types of errors related to service accounts. These errors
    # appear to be the same except for their messages, but they are caused by
    # different problems and both have unhelpful error messages. Moreover,
    # the error type belongs to PyOpenSSL, which is not necessarily installed.
    if 'mac verify failure' in str(e):
      _OutputAndExit("Encountered an error while refreshing access token." +
          " If you are using a service account,\nplease verify that the " +
          "gs_service_key_file_password field in your config file," +
          "\n%s, is correct." % GetConfigFilePath())
    elif 'asn1 encoding routines' in str(e):
      _OutputAndExit("Encountered an error while refreshing access token." +
          " If you are using a service account,\nplease verify that the " +
          "gs_service_key_file field in your config file,\n%s, is correct."
          % GetConfigFilePath())
    _HandleUnknownFailure(e)


if __name__ == '__main__':
  sys.exit(main())
