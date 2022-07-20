#!/usr/bin/env python

import sys
import subprocess
from subprocess import Popen, PIPE, DEVNULL, TimeoutExpired
import shlex
import signal
import itertools
import timeit

import numpy as np


def search(timeout, system, interpretation, dimension, resultwidth):
    cmd = f'python prover/main.py {system} -i {interpretation} -d {dimension} -rw {resultwidth} -any -work 8'
    proc = Popen(shlex.split(cmd), stdout=DEVNULL, stderr=DEVNULL)
    try:
        out = proc.communicate(timeout=timeout)[0]
        if proc.returncode == 19:
            return True
        elif proc.returncode in (11, 29):
            return False
        else:
            sys.exit(f'\nERROR: Unknown return code: {proc.returncode}')
    except TimeoutExpired:
        proc.send_signal(signal.SIGINT)
        proc.communicate()
        return False


def main():
    D = 7
    RW = 8
    timeout = 30
    repeat = 25
    print(f'D <= {D}\n'
          f'RW <= {RW}\n'
          f'timeout: {timeout}\n'
          f'repeat: {repeat}')
    instances = (int(x) for x in sys.argv[1:]) if len(sys.argv) > 1 else range(1, 12)
    for instance in (f'{x:0=2d}' for x in instances):
        print(instance, end='')
        for interpretation in ('natural', 'arctic'):
            for dimension, resultwidth in itertools.product(range(1, D + 1), range(2, RW + 1)):
                result = search(timeout, f'relative/collatz-T-{instance}.srs', interpretation, dimension, resultwidth)
                if result:
                    stmt = f"search(None, 'relative/collatz-T-{instance}.srs', '{interpretation}', {dimension}, {resultwidth})"
                    times = timeit.repeat(stmt, repeat=repeat, number=1, globals=globals())
                    medtime = np.median(times)
                    print(f'\t\t{interpretation} {dimension} {resultwidth} {medtime:6.2f}s', end='')
                    break
            else:
                print(f'\t\t{interpretation} - - {"-":^7}', end='')
        print()


if __name__ == '__main__':
    main()
