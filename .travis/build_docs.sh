#!/bin/bash

set -e

THISDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BASEDIR=${TRAVIS_BUILD_DIR:-${THISDIR}/..}
BUILDDIR=${1:-${BASEDIR}/build}

pushd ${BASEDIR}
./scripts/bash/travis_prepare_compiler_setup.sh 4.9
./dune-common/bin/dunecontrol --builddir=${BUILDDIR} configure
for i in common la grid functions ; do
  ./dune-common/bin/dunecontrol --builddir=${BUILDDIR} --only=dune-xt-${i} bexec make doc
done

popd

