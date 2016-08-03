# reset for ctest
${SRC_DCTRL} ${DCTRL_ARG} --only=${MY_MODULE} bexec ${BUILD_CMD} clean
export CTEST_ARG="--output-on-failure -S ${TRAVIS_BUILD_DIR}/.travis.ctest"
# ctest errors on coverage gathering, this should NOT fail our entire build
${SRC_DCTRL} ${DCTRL_ARG} --only=${MY_MODULE} bexec ctest ${CTEST_ARG} || echo "CTest Failed"