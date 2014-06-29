"""Generated client library for sqladmin version v1beta3."""

from googlecloudapis.apitools.base.py import base_api
from googlecloudapis.sqladmin.v1beta3 import sqladmin_v1beta3_messages as messages


class SqladminV1beta3(base_api.BaseApiClient):
  """Generated client library for service sqladmin version v1beta3."""

  MESSAGES_MODULE = messages

  _PACKAGE = u'sqladmin'
  _SCOPES = [u'https://www.googleapis.com/auth/cloud-platform', u'https://www.googleapis.com/auth/sqlservice.admin']
  _VERSION = u'v1beta3'
  _CLIENT_ID = ''
  _CLIENT_SECRET = ''
  _USER_AGENT = ''
  _CLIENT_CLASS_NAME = u'SqladminV1beta3'
  _URL_VERSION = u'v1beta3'

  def __init__(self, url='', credentials=None,
               get_credentials=True, http=None, model=None,
               log_request=False, log_response=False,
               credentials_args=None, default_global_params=None):
    """Create a new sqladmin handle."""
    url = url or u'https://www.googleapis.com/sql/v1beta3/'
    super(SqladminV1beta3, self).__init__(
        url, credentials=credentials,
        get_credentials=get_credentials, http=http, model=model,
        log_request=log_request, log_response=log_response,
        credentials_args=credentials_args,
        default_global_params=default_global_params)
    self.backupRuns = self.BackupRunsService(self)
    self.flags = self.FlagsService(self)
    self.instances = self.InstancesService(self)
    self.operations = self.OperationsService(self)
    self.sslCerts = self.SslCertsService(self)
    self.tiers = self.TiersService(self)

  class BackupRunsService(base_api.BaseApiService):
    """Service class for the backupRuns resource."""

    def __init__(self, client):
      super(SqladminV1beta3.BackupRunsService, self).__init__(client)
      self._method_configs = {
          'Get': base_api.ApiMethodInfo(
              http_method=u'GET',
              method_id=u'sql.backupRuns.get',
              ordered_params=[u'project', u'instance', u'backupConfiguration', u'dueTime'],
              path_params=[u'backupConfiguration', u'instance', u'project'],
              query_params=[u'dueTime'],
              relative_path=u'projects/{project}/instances/{instance}/backupRuns/{backupConfiguration}',
              request_field='',
              request_type_name=u'SqlBackupRunsGetRequest',
              response_type_name=u'BackupRun',
              supports_download=False,
          ),
          'List': base_api.ApiMethodInfo(
              http_method=u'GET',
              method_id=u'sql.backupRuns.list',
              ordered_params=[u'project', u'instance', u'backupConfiguration'],
              path_params=[u'instance', u'project'],
              query_params=[u'backupConfiguration', u'maxResults', u'pageToken'],
              relative_path=u'projects/{project}/instances/{instance}/backupRuns',
              request_field='',
              request_type_name=u'SqlBackupRunsListRequest',
              response_type_name=u'BackupRunsListResponse',
              supports_download=False,
          ),
          }

      self._upload_configs = {
          }

    def Get(self, request, global_params=None):
      """Retrieves a resource containing information about a backup run.

      Args:
        request: (SqlBackupRunsGetRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (BackupRun) The response message.
      """
      config = self.GetMethodConfig('Get')
      return self._RunMethod(
          config, request, global_params=global_params)

    def List(self, request, global_params=None):
      """Lists all backup runs associated with a given instance and configuration in the reverse chronological order of the enqueued time.

      Args:
        request: (SqlBackupRunsListRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (BackupRunsListResponse) The response message.
      """
      config = self.GetMethodConfig('List')
      return self._RunMethod(
          config, request, global_params=global_params)

  class FlagsService(base_api.BaseApiService):
    """Service class for the flags resource."""

    def __init__(self, client):
      super(SqladminV1beta3.FlagsService, self).__init__(client)
      self._method_configs = {
          'List': base_api.ApiMethodInfo(
              http_method=u'GET',
              method_id=u'sql.flags.list',
              ordered_params=[],
              path_params=[],
              query_params=[],
              relative_path=u'flags',
              request_field='',
              request_type_name=u'SqlFlagsListRequest',
              response_type_name=u'FlagsListResponse',
              supports_download=False,
          ),
          }

      self._upload_configs = {
          }

    def List(self, request, global_params=None):
      """List all available database flags for Google Cloud SQL instances.

      Args:
        request: (SqlFlagsListRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (FlagsListResponse) The response message.
      """
      config = self.GetMethodConfig('List')
      return self._RunMethod(
          config, request, global_params=global_params)

  class InstancesService(base_api.BaseApiService):
    """Service class for the instances resource."""

    def __init__(self, client):
      super(SqladminV1beta3.InstancesService, self).__init__(client)
      self._method_configs = {
          'Clone': base_api.ApiMethodInfo(
              http_method=u'POST',
              method_id=u'sql.instances.clone',
              ordered_params=[u'project'],
              path_params=[u'project'],
              query_params=[],
              relative_path=u'projects/{project}/instances/clone',
              request_field=u'instancesCloneRequest',
              request_type_name=u'SqlInstancesCloneRequest',
              response_type_name=u'InstancesCloneResponse',
              supports_download=False,
          ),
          'Delete': base_api.ApiMethodInfo(
              http_method=u'DELETE',
              method_id=u'sql.instances.delete',
              ordered_params=[u'project', u'instance'],
              path_params=[u'instance', u'project'],
              query_params=[],
              relative_path=u'projects/{project}/instances/{instance}',
              request_field='',
              request_type_name=u'SqlInstancesDeleteRequest',
              response_type_name=u'InstancesDeleteResponse',
              supports_download=False,
          ),
          'Export': base_api.ApiMethodInfo(
              http_method=u'POST',
              method_id=u'sql.instances.export',
              ordered_params=[u'project', u'instance'],
              path_params=[u'instance', u'project'],
              query_params=[],
              relative_path=u'projects/{project}/instances/{instance}/export',
              request_field=u'instancesExportRequest',
              request_type_name=u'SqlInstancesExportRequest',
              response_type_name=u'InstancesExportResponse',
              supports_download=False,
          ),
          'Get': base_api.ApiMethodInfo(
              http_method=u'GET',
              method_id=u'sql.instances.get',
              ordered_params=[u'project', u'instance'],
              path_params=[u'instance', u'project'],
              query_params=[],
              relative_path=u'projects/{project}/instances/{instance}',
              request_field='',
              request_type_name=u'SqlInstancesGetRequest',
              response_type_name=u'DatabaseInstance',
              supports_download=False,
          ),
          'Import': base_api.ApiMethodInfo(
              http_method=u'POST',
              method_id=u'sql.instances.import',
              ordered_params=[u'project', u'instance'],
              path_params=[u'instance', u'project'],
              query_params=[],
              relative_path=u'projects/{project}/instances/{instance}/import',
              request_field=u'instancesImportRequest',
              request_type_name=u'SqlInstancesImportRequest',
              response_type_name=u'InstancesImportResponse',
              supports_download=False,
          ),
          'Insert': base_api.ApiMethodInfo(
              http_method=u'POST',
              method_id=u'sql.instances.insert',
              ordered_params=[u'project'],
              path_params=[u'project'],
              query_params=[],
              relative_path=u'projects/{project}/instances',
              request_field='<request>',
              request_type_name=u'DatabaseInstance',
              response_type_name=u'InstancesInsertResponse',
              supports_download=False,
          ),
          'List': base_api.ApiMethodInfo(
              http_method=u'GET',
              method_id=u'sql.instances.list',
              ordered_params=[u'project'],
              path_params=[u'project'],
              query_params=[u'maxResults', u'pageToken'],
              relative_path=u'projects/{project}/instances',
              request_field='',
              request_type_name=u'SqlInstancesListRequest',
              response_type_name=u'InstancesListResponse',
              supports_download=False,
          ),
          'Patch': base_api.ApiMethodInfo(
              http_method=u'PATCH',
              method_id=u'sql.instances.patch',
              ordered_params=[u'project', u'instance'],
              path_params=[u'instance', u'project'],
              query_params=[],
              relative_path=u'projects/{project}/instances/{instance}',
              request_field='<request>',
              request_type_name=u'DatabaseInstance',
              response_type_name=u'InstancesUpdateResponse',
              supports_download=False,
          ),
          'ResetSslConfig': base_api.ApiMethodInfo(
              http_method=u'POST',
              method_id=u'sql.instances.resetSslConfig',
              ordered_params=[u'project', u'instance'],
              path_params=[u'instance', u'project'],
              query_params=[],
              relative_path=u'projects/{project}/instances/{instance}/resetSslConfig',
              request_field='',
              request_type_name=u'SqlInstancesResetSslConfigRequest',
              response_type_name=u'InstancesResetSslConfigResponse',
              supports_download=False,
          ),
          'Restart': base_api.ApiMethodInfo(
              http_method=u'POST',
              method_id=u'sql.instances.restart',
              ordered_params=[u'project', u'instance'],
              path_params=[u'instance', u'project'],
              query_params=[],
              relative_path=u'projects/{project}/instances/{instance}/restart',
              request_field='',
              request_type_name=u'SqlInstancesRestartRequest',
              response_type_name=u'InstancesRestartResponse',
              supports_download=False,
          ),
          'RestoreBackup': base_api.ApiMethodInfo(
              http_method=u'POST',
              method_id=u'sql.instances.restoreBackup',
              ordered_params=[u'project', u'instance', u'backupConfiguration', u'dueTime'],
              path_params=[u'instance', u'project'],
              query_params=[u'backupConfiguration', u'dueTime'],
              relative_path=u'projects/{project}/instances/{instance}/restoreBackup',
              request_field='',
              request_type_name=u'SqlInstancesRestoreBackupRequest',
              response_type_name=u'InstancesRestoreBackupResponse',
              supports_download=False,
          ),
          'SetRootPassword': base_api.ApiMethodInfo(
              http_method=u'POST',
              method_id=u'sql.instances.setRootPassword',
              ordered_params=[u'project', u'instance'],
              path_params=[u'instance', u'project'],
              query_params=[],
              relative_path=u'projects/{project}/instances/{instance}/setRootPassword',
              request_field=u'instanceSetRootPasswordRequest',
              request_type_name=u'SqlInstancesSetRootPasswordRequest',
              response_type_name=u'InstancesSetRootPasswordResponse',
              supports_download=False,
          ),
          'Update': base_api.ApiMethodInfo(
              http_method=u'PUT',
              method_id=u'sql.instances.update',
              ordered_params=[u'project', u'instance'],
              path_params=[u'instance', u'project'],
              query_params=[],
              relative_path=u'projects/{project}/instances/{instance}',
              request_field='<request>',
              request_type_name=u'DatabaseInstance',
              response_type_name=u'InstancesUpdateResponse',
              supports_download=False,
          ),
          }

      self._upload_configs = {
          }

    def Clone(self, request, global_params=None):
      """Creates a Cloud SQL instance as a clone of the source instance.

      Args:
        request: (SqlInstancesCloneRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (InstancesCloneResponse) The response message.
      """
      config = self.GetMethodConfig('Clone')
      return self._RunMethod(
          config, request, global_params=global_params)

    def Delete(self, request, global_params=None):
      """Deletes a Cloud SQL instance.

      Args:
        request: (SqlInstancesDeleteRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (InstancesDeleteResponse) The response message.
      """
      config = self.GetMethodConfig('Delete')
      return self._RunMethod(
          config, request, global_params=global_params)

    def Export(self, request, global_params=None):
      """Exports data from a Cloud SQL instance to a Google Cloud Storage bucket as a MySQL dump file.

      Args:
        request: (SqlInstancesExportRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (InstancesExportResponse) The response message.
      """
      config = self.GetMethodConfig('Export')
      return self._RunMethod(
          config, request, global_params=global_params)

    def Get(self, request, global_params=None):
      """Retrieves a resource containing information about a Cloud SQL instance.

      Args:
        request: (SqlInstancesGetRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (DatabaseInstance) The response message.
      """
      config = self.GetMethodConfig('Get')
      return self._RunMethod(
          config, request, global_params=global_params)

    def Import(self, request, global_params=None):
      """Imports data into a Cloud SQL instance from a MySQL dump file in Google Cloud Storage.

      Args:
        request: (SqlInstancesImportRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (InstancesImportResponse) The response message.
      """
      config = self.GetMethodConfig('Import')
      return self._RunMethod(
          config, request, global_params=global_params)

    def Insert(self, request, global_params=None):
      """Creates a new Cloud SQL instance.

      Args:
        request: (DatabaseInstance) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (InstancesInsertResponse) The response message.
      """
      config = self.GetMethodConfig('Insert')
      return self._RunMethod(
          config, request, global_params=global_params)

    def List(self, request, global_params=None):
      """Lists instances under a given project in the alphabetical order of the instance name.

      Args:
        request: (SqlInstancesListRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (InstancesListResponse) The response message.
      """
      config = self.GetMethodConfig('List')
      return self._RunMethod(
          config, request, global_params=global_params)

    def Patch(self, request, global_params=None):
      """Updates settings of a Cloud SQL instance. Caution: This is not a partial update, so you must include values for all the settings that you want to retain. For partial updates, use patch.. This method supports patch semantics.

      Args:
        request: (DatabaseInstance) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (InstancesUpdateResponse) The response message.
      """
      config = self.GetMethodConfig('Patch')
      return self._RunMethod(
          config, request, global_params=global_params)

    def ResetSslConfig(self, request, global_params=None):
      """Deletes all client certificates and generates a new server SSL certificate for the instance. The changes will not take effect until the instance is restarted. Existing instances without a server certificate will need to call this once to set a server certificate.

      Args:
        request: (SqlInstancesResetSslConfigRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (InstancesResetSslConfigResponse) The response message.
      """
      config = self.GetMethodConfig('ResetSslConfig')
      return self._RunMethod(
          config, request, global_params=global_params)

    def Restart(self, request, global_params=None):
      """Restarts a Cloud SQL instance.

      Args:
        request: (SqlInstancesRestartRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (InstancesRestartResponse) The response message.
      """
      config = self.GetMethodConfig('Restart')
      return self._RunMethod(
          config, request, global_params=global_params)

    def RestoreBackup(self, request, global_params=None):
      """Restores a backup of a Cloud SQL instance.

      Args:
        request: (SqlInstancesRestoreBackupRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (InstancesRestoreBackupResponse) The response message.
      """
      config = self.GetMethodConfig('RestoreBackup')
      return self._RunMethod(
          config, request, global_params=global_params)

    def SetRootPassword(self, request, global_params=None):
      """Sets the password for the root user.

      Args:
        request: (SqlInstancesSetRootPasswordRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (InstancesSetRootPasswordResponse) The response message.
      """
      config = self.GetMethodConfig('SetRootPassword')
      return self._RunMethod(
          config, request, global_params=global_params)

    def Update(self, request, global_params=None):
      """Updates settings of a Cloud SQL instance. Caution: This is not a partial update, so you must include values for all the settings that you want to retain. For partial updates, use patch.

      Args:
        request: (DatabaseInstance) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (InstancesUpdateResponse) The response message.
      """
      config = self.GetMethodConfig('Update')
      return self._RunMethod(
          config, request, global_params=global_params)

  class OperationsService(base_api.BaseApiService):
    """Service class for the operations resource."""

    def __init__(self, client):
      super(SqladminV1beta3.OperationsService, self).__init__(client)
      self._method_configs = {
          'Get': base_api.ApiMethodInfo(
              http_method=u'GET',
              method_id=u'sql.operations.get',
              ordered_params=[u'project', u'instance', u'operation'],
              path_params=[u'instance', u'operation', u'project'],
              query_params=[],
              relative_path=u'projects/{project}/instances/{instance}/operations/{operation}',
              request_field='',
              request_type_name=u'SqlOperationsGetRequest',
              response_type_name=u'InstanceOperation',
              supports_download=False,
          ),
          'List': base_api.ApiMethodInfo(
              http_method=u'GET',
              method_id=u'sql.operations.list',
              ordered_params=[u'project', u'instance'],
              path_params=[u'instance', u'project'],
              query_params=[u'maxResults', u'pageToken'],
              relative_path=u'projects/{project}/instances/{instance}/operations',
              request_field='',
              request_type_name=u'SqlOperationsListRequest',
              response_type_name=u'OperationsListResponse',
              supports_download=False,
          ),
          }

      self._upload_configs = {
          }

    def Get(self, request, global_params=None):
      """Retrieves an instance operation that has been performed on an instance.

      Args:
        request: (SqlOperationsGetRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (InstanceOperation) The response message.
      """
      config = self.GetMethodConfig('Get')
      return self._RunMethod(
          config, request, global_params=global_params)

    def List(self, request, global_params=None):
      """Lists all instance operations that have been performed on the given Cloud SQL instance in the reverse chronological order of the start time.

      Args:
        request: (SqlOperationsListRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (OperationsListResponse) The response message.
      """
      config = self.GetMethodConfig('List')
      return self._RunMethod(
          config, request, global_params=global_params)

  class SslCertsService(base_api.BaseApiService):
    """Service class for the sslCerts resource."""

    def __init__(self, client):
      super(SqladminV1beta3.SslCertsService, self).__init__(client)
      self._method_configs = {
          'Delete': base_api.ApiMethodInfo(
              http_method=u'DELETE',
              method_id=u'sql.sslCerts.delete',
              ordered_params=[u'project', u'instance', u'sha1Fingerprint'],
              path_params=[u'instance', u'project', u'sha1Fingerprint'],
              query_params=[],
              relative_path=u'projects/{project}/instances/{instance}/sslCerts/{sha1Fingerprint}',
              request_field='',
              request_type_name=u'SqlSslCertsDeleteRequest',
              response_type_name=u'SslCertsDeleteResponse',
              supports_download=False,
          ),
          'Get': base_api.ApiMethodInfo(
              http_method=u'GET',
              method_id=u'sql.sslCerts.get',
              ordered_params=[u'project', u'instance', u'sha1Fingerprint'],
              path_params=[u'instance', u'project', u'sha1Fingerprint'],
              query_params=[],
              relative_path=u'projects/{project}/instances/{instance}/sslCerts/{sha1Fingerprint}',
              request_field='',
              request_type_name=u'SqlSslCertsGetRequest',
              response_type_name=u'SslCert',
              supports_download=False,
          ),
          'Insert': base_api.ApiMethodInfo(
              http_method=u'POST',
              method_id=u'sql.sslCerts.insert',
              ordered_params=[u'project', u'instance'],
              path_params=[u'instance', u'project'],
              query_params=[],
              relative_path=u'projects/{project}/instances/{instance}/sslCerts',
              request_field=u'sslCertsInsertRequest',
              request_type_name=u'SqlSslCertsInsertRequest',
              response_type_name=u'SslCertsInsertResponse',
              supports_download=False,
          ),
          'List': base_api.ApiMethodInfo(
              http_method=u'GET',
              method_id=u'sql.sslCerts.list',
              ordered_params=[u'project', u'instance'],
              path_params=[u'instance', u'project'],
              query_params=[],
              relative_path=u'projects/{project}/instances/{instance}/sslCerts',
              request_field='',
              request_type_name=u'SqlSslCertsListRequest',
              response_type_name=u'SslCertsListResponse',
              supports_download=False,
          ),
          }

      self._upload_configs = {
          }

    def Delete(self, request, global_params=None):
      """Deletes the SSL certificate. The change will not take effect until the instance is restarted.

      Args:
        request: (SqlSslCertsDeleteRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (SslCertsDeleteResponse) The response message.
      """
      config = self.GetMethodConfig('Delete')
      return self._RunMethod(
          config, request, global_params=global_params)

    def Get(self, request, global_params=None):
      """Retrieves a particular SSL certificate. Does not include the private key (required for usage). The private key must be saved from the response to initial creation.

      Args:
        request: (SqlSslCertsGetRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (SslCert) The response message.
      """
      config = self.GetMethodConfig('Get')
      return self._RunMethod(
          config, request, global_params=global_params)

    def Insert(self, request, global_params=None):
      """Creates an SSL certificate and returns it along with the private key and server certificate authority. The new certificate will not be usable until the instance is restarted.

      Args:
        request: (SqlSslCertsInsertRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (SslCertsInsertResponse) The response message.
      """
      config = self.GetMethodConfig('Insert')
      return self._RunMethod(
          config, request, global_params=global_params)

    def List(self, request, global_params=None):
      """Lists all of the current SSL certificates for the instance.

      Args:
        request: (SqlSslCertsListRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (SslCertsListResponse) The response message.
      """
      config = self.GetMethodConfig('List')
      return self._RunMethod(
          config, request, global_params=global_params)

  class TiersService(base_api.BaseApiService):
    """Service class for the tiers resource."""

    def __init__(self, client):
      super(SqladminV1beta3.TiersService, self).__init__(client)
      self._method_configs = {
          'List': base_api.ApiMethodInfo(
              http_method=u'GET',
              method_id=u'sql.tiers.list',
              ordered_params=[u'project'],
              path_params=[u'project'],
              query_params=[],
              relative_path=u'projects/{project}/tiers',
              request_field='',
              request_type_name=u'SqlTiersListRequest',
              response_type_name=u'TiersListResponse',
              supports_download=False,
          ),
          }

      self._upload_configs = {
          }

    def List(self, request, global_params=None):
      """Lists all available service tiers for Google Cloud SQL, for example D1, D2. For related information, see Pricing.

      Args:
        request: (SqlTiersListRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (TiersListResponse) The response message.
      """
      config = self.GetMethodConfig('List')
      return self._RunMethod(
          config, request, global_params=global_params)
