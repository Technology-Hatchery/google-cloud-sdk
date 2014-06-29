from boto.auth_handler import AuthHandler
from boto.auth_handler import NotReadyToAuthenticate 
import oauth2_client
import oauth2_helper
from gslib.cred_types import CredTypes

IS_SERVICE_ACCOUNT = False

class OAuth2Auth(AuthHandler):

  capability = ['google-oauth2', 's3']

  def __init__(self, path, config, provider):
    if (provider.name == 'google'
        and config.has_option('Credentials', 'gs_oauth2_refresh_token')):
      self.oauth2_client = oauth2_helper.OAuth2ClientFromBotoConfig(config)
    else:
      raise NotReadyToAuthenticate()

  def add_auth(self, http_request):
    http_request.headers['Authorization'] = \
        self.oauth2_client.GetAuthorizationHeader()

class OAuth2ServiceAccountAuth(AuthHandler):
  
  capability = ['google-oauth2', 's3']

  def __init__(self, path, config, provider):
    if (provider.name == 'google' 
        and config.has_option('Credentials', 'gs_service_client_id') 
        and config.has_option('Credentials', 'gs_service_key_file')):
      self.oauth2_client = oauth2_helper.OAuth2ClientFromBotoConfig(config, 
          cred_type=CredTypes.OAUTH2_SERVICE_ACCOUNT)
      
      # If we make it to this point, then we will later attempt to authenticate
      # as a service account based on how the boto auth plugins work. This is
      # global so that command.py can access this value once it's set.
      # TODO: replace this approach with a way to get the current plugin
      # from boto so that we don't have to have global variables.
      global IS_SERVICE_ACCOUNT
      IS_SERVICE_ACCOUNT = True
    else:
      raise NotReadyToAuthenticate()
 
  def add_auth(self, http_request):
    http_request.headers['Authorization'] = \
        self.oauth2_client.GetAuthorizationHeader()
         
