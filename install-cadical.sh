#!/usr/bin/env bash

rt=$(pwd)
mkdir -p tools/

cd tools

rm -rf cadical
git clone https://github.com/arminbiere/cadical
cd cadical
./configure && make
ln -sf "$rt/tools/cadical/build/cadical" "$rt/cadical"

cd ..
