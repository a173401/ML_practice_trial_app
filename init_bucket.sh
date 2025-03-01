#!/bin/bash

ACCESS_KEY=$(head /dev/urandom | tr -dc A-Za-z0-9 | head -c 20 ; echo '')
SECRET_KEY=$(head /dev/urandom | tr -dc A-Za-z0-9 | head -c 40 ; echo '')
echo 'Generated ACCESS_KEY: '$ACCESS_KEY
echo 'Generated SECRET_KEY: '$SECRET_KEY


mc alias set minio http://minio:9000 ${MINIO_ROOT_USER} ${MINIO_ROOT_PASSWORD} &&
if ! mc stat minio/attachments &> /dev/null; then
    mc mb minio/attachments
    mc ilm add minio/attachments --expire-days 1
    mc admin accesskey create minio/ ${MINIO_ROOT_USER} --access-key $ACCESS_KEY --secret-key $SECRET_KEY
else
    echo 'Bucket already exists'
fi