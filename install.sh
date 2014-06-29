#!/bin/sh
#
# Copyright 2013 Google Inc. All Rights Reserved.
#

echo Welcome to the Google Cloud SDK!

if [ -z "$CLOUDSDK_PYTHON" ]; then
  if [ -z "$(which python)" ]; then
    echo
    echo "To use the Google Cloud SDK, you must have Python installed and on your PATH."
    echo "As an alternative, you may also set the CLOUDSDK_PYTHON environment variable"
    echo "to the location of your Python executable."
    exit 1
  fi
  CLOUDSDK_PYTHON="python"
fi

# <cloud-sdk-preamble>
#
#  CLOUDSDK_ROOT_DIR      (a)  installation root dir
#  CLOUDSDK_PYTHON        (u)  python interpreter path
#  CLOUDSDK_PYTHON_ARGS   (u)  python interpreter arguments
#
# (a) always defined by the preamble
# (u) user definition overrides preamble

# Determines the real cloud sdk root dir given the script path.
# Would be easier with a portable "readlink -f".
_cloudsdk_root_dir() {
  case $1 in
  /*)   _cloudsdk_path=$1
        ;;
  */*)  _cloudsdk_path=$PWD/$1
        ;;
  *)    _cloudsdk_path=$(which "$1")
        case $_cloudsdk_path in
        /*) ;;
        *)  _cloudsdk_path=$PWD/$_cloudsdk_path ;;
        esac
        ;;
  esac
  _cloudsdk_dir=0
  while :
  do
    while _cloudsdk_link=$(readlink "$_cloudsdk_path")
    do
      case $_cloudsdk_link in
      /*) _cloudsdk_path=$_cloudsdk_link ;;
      *)  _cloudsdk_path=$(dirname "$_cloudsdk_path")/$_cloudsdk_link ;;
      esac
    done
    case $_cloudsdk_dir in
    1)  break ;;
    esac
    _cloudsdk_dir=1
    _cloudsdk_path=$(dirname "$_cloudsdk_path")
  done
  while :
  do  case $_cloudsdk_path in
      */.)    _cloudsdk_path=$(dirname "$_cloudsdk_path")
              ;;
      */bin)  dirname "$_cloudsdk_path"
              break
              ;;
      *)      echo "$_cloudsdk_path"
              break
              ;;
      esac
  done
}
CLOUDSDK_ROOT_DIR=$(_cloudsdk_root_dir "$0")

[ -z "$CLOUDSDK_PYTHON" ] &&
  CLOUDSDK_PYTHON=python

[ -n "$_always_use_site_packages" ] && export CLOUDSDK_PYTHON_SITEPACKAGES=1

[ -z "$CLOUDSDK_PYTHON_ARGS" -a -z "$CLOUDSDK_PYTHON_SITEPACKAGES" ] &&
  CLOUDSDK_PYTHON_ARGS=-S

export CLOUDSDK_ROOT_DIR CLOUDSDK_PYTHON_ARGS

# </cloud-sdk-preamble>


"$CLOUDSDK_PYTHON" $CLOUDSDK_PYTHON_ARGS "${CLOUDSDK_ROOT_DIR}/bin/bootstrapping/install.py" "$@"
