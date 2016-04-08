#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

pushd ${DIR}
chmod 600 github_deploy.rsa
mv github_deploy.rsa ~/.ssh/id_rsa
mv github_deploy.pub ~/.ssh/id_rsa.pub
popd
