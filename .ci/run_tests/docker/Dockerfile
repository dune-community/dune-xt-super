ARG BASE
FROM $BASE
#
# RUN ${DUNE_VENV_ACTIVATE} && \
#     ${SRC_DCTRL} ${BLD} --only=${MY_MODULE} make test_binaries
RUN echo '${DUNE_VENV_ACTIVATE}\n ${SRC_DCTRL} ${BLD} --only=${MY_MODULE} bexec ctest -V -L ^builder_${TESTS}$' \
        > /usr/local/bin/run_tests.bash && \
    chmod +x /usr/local/bin/run_tests.bash
ADD env.sh /usr/share/env.sh

WORKDIR ${SUPERDIR}
ADD entrypoint.sh /usr/local/bin/
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
