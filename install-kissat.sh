#!/usr/bin/env bash

rt=$(pwd)
mkdir -p tools/

cd tools

rm -rf kissat
git clone https://github.com/arminbiere/kissat
cd kissat
./configure && make
ln -sf "$rt/tools/kissat/build/kissat" "$rt/kissat"

cd ..
