#!/bin/bash
set -e
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

KEY=${1}
IV=${2}
TESTLOGS=${TRAVIS_REPO_SLUG/\//_}-testlogs
RSAKEY=${3:-${TESTLOGS}}.rsa.enc
echo "SSH key init: ${RSAKEY}"
pushd ${DIR}
openssl aes-256-cbc -K ${KEY} -iv ${IV} -in ${RSAKEY} -out ~/.ssh/id_rsa -d
chmod 600 ~/.ssh/id_rsa
popd
