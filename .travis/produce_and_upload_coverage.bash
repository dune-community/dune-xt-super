#!/bin/bash
if [[ "${CC}" == "gcc"* ]] ; then
    wget https://codecov.io/bash -O codecov
    lcov --gcov-tool ${GCOV} -b ${SUPERDIR}/${MY_MODULE} -d ${DUNE_BUILD_DIR}/${MY_MODULE} -c -o ${HOME}/tested.lcov --no-external --quiet
    lcov --gcov-tool ${GCOV} -a ${HOME}/baseline.lcov -a ${HOME}/tested.lcov -o ${HOME}/full.lcov --quiet
    bash ./codecov -v -f ${HOME}/full.lcov -R ${SUPERDIR}/${MY_MODULE}
fi
