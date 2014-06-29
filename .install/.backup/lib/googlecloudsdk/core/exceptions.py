# Copyright 2014 Google Inc. All Rights Reserved.

"""Base exceptions for the Cloud SDK."""


class _Error(Exception):
  """A base exception for all Cloud SDK errors.

  This exception should not be used directly.
  """
  pass


class InternalError(_Error):
  """A base class for all non-recoverable internal errors."""
  pass


class Error(_Error):
  """A base exception for all user recoverable errors.

  Any exception that extends this class will not be printed with a stack trace
  when running from CLI mode.  Instead it will be shows with a message of how
  the user can correct this problem.

  All exceptions of this type must have a message for the user.
  """
  pass
