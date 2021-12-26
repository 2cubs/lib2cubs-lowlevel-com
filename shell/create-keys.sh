#!/usr/bin/env bash

_NAME="${1}";
_DAYS=365;
_ENC_ALG='rsa';
_ENC_SIZE=4096;
_DOMAIN='localhost';
_TO_PATH="${2:-./}"

#mkdir "${_TO_PATH}";

if [ -z "${_NAME}" ]; then
  echo -ne "The first parameter \"name\" must specified (for example: \"server\", or \"client\").\n";
  exit 1;
fi;

openssl req -x509 -nodes -sha256 \
    -newkey "${_ENC_ALG}:${_ENC_SIZE}" \
    -subj "/CN=${_DOMAIN}" \
    -days "${_DAYS}" \
    -keyout "${_TO_PATH}/${_NAME}.key" \
    -out "${_TO_PATH}/${_NAME}.crt";

cat "${_TO_PATH}/${_NAME}.key" > "${_TO_PATH}/${_NAME}-bundle.pem" && cat "${_TO_PATH}/${_NAME}.crt" >> "${_TO_PATH}/${_NAME}-bundle.pem" && rm -v "${_TO_PATH}/${_NAME}."*;


