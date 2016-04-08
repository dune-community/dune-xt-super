#!/bin/bash

set -e

THISDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BASEDIR=${TRAVIS_BUILD_DIR:-${THISDIR}/..}
ID=${TRAVIS_TAG:-${TRAVIS_BRANCH}}

${THISDIR}/init_sshkey.sh
pushd ${BASEDIR}

git clone git@github.com:dune-community/dune-community.github.io.git site

./build_docs.sh ${PWD}/build

cd site
git config user.name "DUNE Community Bot"
git config user.email "dune-community.bot@wwu.de"

for i in common la grid functions ; do
  TARGET=docs/dune-xt-${i}/${ID}/
  mkdir -p ${TARGET}
  rsync -a --delete  ${BUILDDIR}/dune-xt-${i}/doc/doxygen/html/ ${TARGET}/
  git add ${TARGET}
done

git commit -m "Updated documentation for dune-xt ${ID}"
git push

popd
