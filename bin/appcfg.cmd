@echo off
rem Copyright 2013 Google Inc. All Rights Reserved.

cmd /c "python "%~dp0bootstrapping\prerun.py" --command-name=appcfg-java --component-id=gae-java --check-credentials --check-updates"
IF %ERRORLEVEL% NEQ 0 (
  EXIT /B %ERRORLEVEL%
)

SETLOCAL

set TMPFILE=%APPDATA%\gcloud\tmp-env-info-%RANDOM%.txt

cmd /c "python "%~dp0bootstrapping\print_env_info.py" gae_java_path" > "%TMPFILE%"
IF %ERRORLEVEL% NEQ 0 (
  EXIT /B %ERRORLEVEL%
)

set /p credential_path= < "%TMPFILE%"
del "%TMPFILE%"

cmd /c ""%~dp0..\platform/appengine-java-sdk\bin\appcfg.cmd" --oauth2 --oauth2_config_file="%credential_path%" %*"
IF %ERRORLEVEL% NEQ 0 (
  EXIT /B %ERRORLEVEL%
)

ENDLOCAL
