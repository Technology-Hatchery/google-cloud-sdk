@echo off
rem Copyright 2013 Google Inc. All Rights Reserved.

cmd /c "python "%~dp0bootstrapping\prerun.py" --command-name=dev_appserver-java --component-id=gae-java --check-updates"
IF %ERRORLEVEL% NEQ 0 (
  EXIT /B %ERRORLEVEL%
)

cmd /c ""%~dp0..\platform/appengine-java-sdk\bin\dev_appserver.cmd" --disable_update_check %*"
