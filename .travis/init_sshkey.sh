#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

pushd ${DIR}
openssl aes-256-cbc -K $encrypted_862ca47045d1_key -iv $encrypted_862ca47045d1_iv -in github_deploy.rsa.enc -out github_deploy.rsa -d
chmod 600 github_deploy.rsa
mv github_deploy.rsa ~/.ssh/id_rsa
mv github_deploy.pub ~/.ssh/id_rsa.pub
popd
