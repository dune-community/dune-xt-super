#!/bin/bash

set -e
. dune_utils.bash
getOptsFile $2
${CMD} --only=$1 --opts=${OPTS} --use-cmake all
