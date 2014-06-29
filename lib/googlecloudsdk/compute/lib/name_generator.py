# Copyright 2014 Google Inc. All Rights Reserved.

"""A module for generating resource names."""
import cStringIO
import random
import string

_LENGTH = 12
_BEGIN_ALPHABET = string.ascii_lowercase
_END_ALPHABET = _BEGIN_ALPHABET + string.digits
_ALPHABET = _END_ALPHABET + '-'


def GenerateRandomName():
  """Generates a random string.

  Returns:
    The returned string will be 12 characters long and will begin with
    a lowercase letter followed by 10 characters drawn from the set
    [-a-z0-9] and finally a character drawn from the set [a-z0-9].
  """
  buf = cStringIO.StringIO()
  buf.write(random.choice(_BEGIN_ALPHABET))
  for _ in xrange(_LENGTH - 2):
    buf.write(random.choice(_ALPHABET))
  buf.write(random.choice(_END_ALPHABET))
  return buf.getvalue()
