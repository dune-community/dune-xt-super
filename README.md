```
# This file is part of the dune-xt-super project:
#   https://github.com/dune-community/dune-xt-super
# The copyright lies with the authors of this file (see below).
# License: BSD 2-Clause License (http://opensource.org/licenses/BSD-2-Clause)
# Authors:
#   Felix Schindler (2017)
```

dune-xt-super serves as a demonstration and testing module for:

* [dune-xt](https://zivgitlab.uni-muenster.de/ag-ohlberger/dune-community/dune-xt)
* [dune-xt-data](https://github.com/dune-community/dune-xt-data)

In order to build everything, do the following:

* Initialize all submodules:

  ```
  git submodule update --init --recursive
  ```
  
* Take a look at `config.opts/` and find settings and a compiler which suits your
  system, e.g. `config.opts/gcc-debug`. Select one of those options by defining
  
  ```
  export OPTS=gcc-debug
  ```
  If you have the `ninja` generator installed we recommend to make use of it by
  selecting `OPTS=gcc-debug.ninja`, which usually speeds up builds significantly.
  
* Call

  ```
  ./local/bin/gen_path.py
  ```
  
  to generate a file `PATH.sh` which defines a local build environment. From now 
  on you should source this file whenever you plan to work on this project, e.g.:
  
  ```
  source PATH.sh
  ```

* Download and build all external libraries by calling (this _might_ take some time):

  ```
  ./local/bin/download_external_libraries.py
  ./local/bin/build_external_libraries.py
  ```
  
* Build all DUNE modules using `cmake` and the selected options (this _will_ take
  some time):

  ```
  ./dune-common/bin/dunecontrol --opts=config.opts/$OPTS --builddir=$PWD/build-$OPTS all
  ```
  
  This creates a directory corresponding to the selected options (e.g. `build-gcc-debug`)
  which contains a subfolder for each DUNE module. See the `dune/foo/test` subfolders for
  tests, e.g.,
  
  ```
  build-gcc-debug/dune-xt-common/dune/xt/common/test/
  ```
