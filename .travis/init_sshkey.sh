#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

KEY=${1}
IV=${2}
SLUG=${TRAVIS_REPO_SLUG/\//_}
RSAKEY=${3:-SLUG}.rsa.enc
pushd ${DIR}
openssl aes-256-cbc -K ${KEY} -iv ${IV} -in ${RSAKEY} -out ~/.ssh/id_rsa -d
chmod 600 ~/.ssh/id_rsa
popd
