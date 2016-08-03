#!/bin/bash
if [[ "${CC}" == "gcc"* ]] ; then
    wget https://codecov.io/bash -O codecov
    lcov --gcov-tool ${GCOV} -b ${HOME}/src/${MY_MODULE} -d ${DUNE_BUILD_DIR}/${MY_MODULE} -c -o ${HOME}/tested.lcov --no-external
    lcov --gcov-tool ${GCOV} -a ${HOME}/baseline.lcov -a ${HOME}/tested.lcov -o ${HOME}/full.lcov
    bash ./codecov -v -f ${HOME}/full.lcov -R ${HOME}/src/${MY_MODULE}
fi