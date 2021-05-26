#!/usr/bin/env python

import sys
import subprocess
from subprocess import Popen, PIPE, DEVNULL, TimeoutExpired
import shlex
import re
import signal
import itertools
import timeit

import numpy as np


def search(timeout, system, interpretation, dimension, resultwidth, phasesaving, workers):
    phase = '-phase' if phasesaving else ''
    work = f'-work {workers}' if workers > 1 else f'-work 1 -noshuf'
    cmd = f'python prover/main.py {system} -i {interpretation} -d {dimension} -rw {resultwidth} -any -once {phase} {work}'
    proc = Popen(shlex.split(cmd), stdout=DEVNULL, stderr=PIPE, text=True)
    try:
        out = proc.communicate(timeout=timeout)[1]
        if proc.returncode in (11, 19):
            return (True, float(re.search('SAT \(Attempt (?:.*), (.*) s\)', out).group(1)))
        else:
            sys.exit(f'\nERROR: Unexpected return code: {proc.returncode}')
    except TimeoutExpired:
        proc.send_signal(signal.SIGINT)
        proc.communicate()
        return (False, timeout)


results = []


def main():
    timeout = 120
    repeat = 25
    print(f'timeout: {timeout}\n'
          f'repeat: {repeat}')
    experiments = [
        ('relative/farkas.srs', 'arctic', 5, 8),
        ('relative/collatz-T-01.srs', 'arctic', 3, 5),
        ('relative/collatz-T-03.srs', 'arctic', 3, 4),
        ('relative/collatz-T-08.srs', 'matrix', 4, 4),
        ('relative/collatz-T-11.srs', 'matrix', 4, 4),
        ('relative/collatz-T-11.srs', 'arctic', 4, 3),
        ('relative/collatz-C-6mod8-2.srs', 'matrix', 3, 11),
        ('relative/collatz-T-3mod8-2.srs', 'arctic', 3, 12)
    ]
    print('\t\t\t\t\t\t\tphase\t\t\t\tnegative')
    print('\t\t\t\t\t\t\tsingle\t\tmultiple\tsingle\t\tmultiple')
    for e in experiments:
        instance, interpretation, dimension, resultwidth = e
        print(f'{instance}\t{interpretation} {dimension:2d} {resultwidth:2d}\t', end='')
        for phase in (True, False):
            for workers in (1, 8):
                results.clear()
                stmt = f"results.append(search({timeout}, '{instance}', '{interpretation}', {dimension}, {resultwidth}, {phase}, {workers}))"
                timeit.repeat(stmt, repeat=repeat, number=1, globals=globals())
                medtime = np.median([time if solved else 2 * time for solved, time in results])
                print(f'\t{medtime:8.2f}s', end='')
        print()


if __name__ == '__main__':
    main()
