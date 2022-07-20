#!/usr/bin/env bash

mkdir -p proofs

function run {
    echo "$1"
    python -u prover/main.py "$@" --printascii > proofs/$(basename "$1" .srs).log 2>&1
}

run relative/zantema.srs            -i natural -d 2 -rw 4
run relative/farkas.srs             -i arctic  -d 5 -rw 8

run relative/collatz-T-01.srs       -i natural -d 3 -rw 4 -any
run relative/collatz-T-02.srs       -i natural -d 1 -rw 2 -any
run relative/collatz-T-03.srs       -i natural -d 4 -rw 2 -any
run relative/collatz-T-04.srs       -i natural -d 1 -rw 3 -any
run relative/collatz-T-05.srs       -i natural -d 1 -rw 2 -any
run relative/collatz-T-06.srs       -i arctic  -d 3 -rw 4 -any
run relative/collatz-T-07.srs       -i arctic  -d 4 -rw 3 -any
run relative/collatz-T-08.srs       -i arctic  -d 2 -rw 5 -any
run relative/collatz-T-09.srs       -i natural -d 2 -rw 2 -any
run relative/collatz-T-10.srs       -i natural -d 3 -rw 3 -any
run relative/collatz-T-11.srs       -i arctic  -d 4 -rw 3 -any

run relative/collatz-S-3mod4.srs    -i natural -d 2 -rw 5

run relative/collatz-C-0mod4.srs    -i natural -d 3 -rw 4
run relative/collatz-C-2mod4.srs    -i natural -d 2 -rw 4
run relative/collatz-T-1mod4.srs    -i natural -d 2 -rw 4 -any
run relative/collatz-T-3mod4.srs    -i natural -d 3 -rw 5 -any

run relative/collatz-C-2mod8.srs    -i natural -d 3 -rw 4 -any
run relative/collatz-C-4mod8.srs    -i natural -d 3 -rw 4 -any
run relative/collatz-C-6mod8.srs    -i arctic  -d 3 -rw 12 -any
run relative/collatz-T-3mod8.srs    -i natural -d 3 -rw 11 -any

run relative/collatz-T-1or5mod8.srs -i natural -d 2 -rw 4 -any
run relative/collatz-T-1or7mod8.srs -i natural -d 3 -rw 7 -any
