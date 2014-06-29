@echo off
rem Copyright 2013 Google Inc. All Rights Reserved.

SETLOCAL

SET LIB_DIR=%~dp0..\lib
IF "%PYTHONPATH%"=="" (
  SET PYTHONPATH=%LIB_DIR%
) ELSE (
  SET PYTHONPATH=%LIB_DIR%;%PYTHONPATH%
)

IF "%CLOUDSDK_PYTHON%"=="" (
  SET CLOUDSDK_PYTHON=python.exe
)

IF "%CLOUDSDK_PYTHON_ARGS%"=="" (
  IF "%CLOUDSDK_PYTHON_SITEPACKAGES%"=="" (
    SET CLOUDSDK_PYTHON_ARGS=-S
  )
)
SET PATH=%~dp0..\bin\sdk;%PATH%

cmd /c "%CLOUDSDK_PYTHON% %CLOUDSDK_PYTHON_ARGS% "%~dp0..\./lib\googlecloudsdk\gcloud\gcloud.py" %*"
IF %ERRORLEVEL% NEQ 0 (
  EXIT /B %ERRORLEVEL%
)

ENDLOCAL
