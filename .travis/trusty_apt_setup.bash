#!/bin/sh
# workaround for https://github.com/travis-ci/travis-ci/issues/5285
sudo -E apt-get install -y -q python-pip python3-pip python3-pytest python-pytest
sudo -E pip3 install -U requests virtualenv cpp-coveralls
sudo -E pip install -U requests virtualenv cpp-coveralls
sudo -E add-apt-repository -y ppa:renemilk/llvm 
# minimally necessary updates
sudo -E apt-get install cpp-4.8 g++-4.8 gcc-4.8 gcc-4.8-base lcov libasan0 libgcc-4.8-dev libstdc++-{5,4.9,4.8}-dev gcc-4.9
sudo -E apt-get update -qq && sudo -E aptitude install -y clang-3.8 clang-format-3.8 lcov
for i in clang-3.7 clang++-3.7 clang-3.8 clang++-3.8 clang-3.9 clang++-3.9 gcc-5 g++-5 : do
    sudo -E ln -s /usr/bin/ccache /usr/lib/ccache/${i}