# Copyright 2014 Google Inc. All Rights Reserved.
"""Defines tool-wide constants."""
import httplib

BYTES_IN_ONE_GB = 2 ** 30

# The maximum number of results that can be returned in a single list
# response.
MAX_RESULTS_PER_PAGE = 500

# Defaults for instance creation.
DEFAULT_ACCESS_CONFIG_NAME = 'external-nat'

DEFAULT_MACHINE_TYPE = 'n1-standard-1'
DEFAULT_NETWORK = 'default'

DEFAULT_IMAGE = 'debian-7-backports'

IMAGE_ALIASES = {
    'centos-6': ('centos-cloud', 'centos-6-v20140415'),
    'debian-7': ('debian-cloud', 'debian-7-wheezy-v20140415'),
    'debian-7-backports': ('debian-cloud',
                           'backports-debian-7-wheezy-v20140415'),
    'rhel-6': ('rhel-cloud', 'rhel-6-v20140415'),
    'sles-11': ('suse-cloud', 'sles-11-sp3-v20140306'),
}

IMAGE_PROJECTS = [
    'centos-cloud',
    'debian-cloud',
    'rhel-cloud',
    'suse-cloud',
]

# SSH-related constants.
DEFAULT_SSH_KEY_FILE = '~/.ssh/google_compute_engine'
SSH_KEYS_METADATA_KEY = 'sshKeys'
MAX_METADATA_VALUE_SIZE_IN_BYTES = 32768
PER_USER_SSH_CONFIG_FILE = '~/.ssh/config'


# Custom help for HTTP error messages.
HTTP_ERROR_TIPS = {
    httplib.UNAUTHORIZED: [
        'try logging in using "gcloud auth login"'
        ],
    httplib.NOT_FOUND: [
        'ensure that resources referenced are spelled correctly',
        ('ensure that the Google Compute Engine API is enabled for '
         'this project at https://cloud.google.com/console'),
        ('ensure that your account is a member of this project at '
         'https://cloud.google.com/console'),
        'ensure that any resources referenced exist',
        ],
    httplib.INTERNAL_SERVER_ERROR: [
        ('these are probably transient errors: try running the command again '
         'in a few minutes'),
        ],
    httplib.BAD_REQUEST: [
        'ensure that you spelled everything correctly',
        'ensure that any resources referenced exist',
        ],
}

_STORAGE_RO = 'https://www.googleapis.com/auth/devstorage.read_only'

DEFAULT_SCOPES = [_STORAGE_RO]

SCOPES = {
    'bigquery': 'https://www.googleapis.com/auth/bigquery',
    'sql': 'https://www.googleapis.com/auth/sqlservice',
    'compute-ro': 'https://www.googleapis.com/auth/compute.readonly',
    'compute-rw': 'https://www.googleapis.com/auth/compute',
    'datastore': 'https://www.googleapis.com/auth/datastore',
    'storage-full': 'https://www.googleapis.com/auth/devstorage.full_control',
    'storage-ro': _STORAGE_RO,
    'storage-rw': 'https://www.googleapis.com/auth/devstorage.read_write',
    'storage-wo': 'https://www.googleapis.com/auth/devstorage.write_only',
    'taskqueue': 'https://www.googleapis.com/auth/taskqueue',
    'userinfo-email': 'https://www.googleapis.com/auth/userinfo.email',
}
