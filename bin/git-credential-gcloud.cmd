@echo off
rem Copyright 2013 Google Inc. All Rights Reserved.
SETLOCAL
set CLOUDSDK_COMPONENT_MANAGER_DISABLE_UPDATE_CHECK=1
call gcloud.cmd auth git-helper "%*"
ENDLOCAL
exit /b %ERRORLEVEL%
