@echo off
rem Copyright 2013 Google Inc. All Rights Reserved.

SETLOCAL

IF "%CLOUDSDK_PYTHON%"=="" (
  SET CLOUDSDK_PYTHON=python.exe
)

cmd /c "%CLOUDSDK_PYTHON% %CLOUDSDK_PYTHON_ARGS% "%~dp0bootstrapping\gsutil.py" %*"

IF %ERRORLEVEL% NEQ 0 (
  EXIT /B %ERRORLEVEL%
)

ENDLOCAL
