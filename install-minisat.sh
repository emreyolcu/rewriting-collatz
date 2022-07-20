#!/usr/bin/env bash

rt=$(pwd)
mkdir -p tools/

cd tools

rm -rf minisat
git clone https://github.com/niklasso/minisat
cd minisat
git apply ../../minisat.patch
make
ln -sf "$rt/tools/minisat/build/release/bin/minisat" "$rt/minisat"

cd ..
