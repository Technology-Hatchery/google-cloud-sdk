@echo off
rem Copyright 2013 Google Inc. All Rights Reserved.

SETLOCAL

IF "%CLOUDSDK_PYTHON%"=="" (
  SET CLOUDSDK_PYTHON=python.exe
)
IF "%CLOUDSDK_PYTHON_ARGS%"=="" (
  IF "%CLOUDSDK_PYTHON_SITEPACKAGES%"=="" (
    SET CLOUDSDK_PYTHON_ARGS=-S
  )
)

cmd /c "%CLOUDSDK_PYTHON% %CLOUDSDK_PYTHON_ARGS% "%~dp0bootstrapping\bq.py" %*"

IF %ERRORLEVEL% NEQ 0 (
  EXIT /B %ERRORLEVEL%
)

ENDLOCAL
