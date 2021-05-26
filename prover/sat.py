import sys
import os
import subprocess
from subprocess import Popen, PIPE, DEVNULL, TimeoutExpired
import time
import shlex
from enum import Enum
import re
import random
import signal
import atexit


Result = Enum('Result', ['SAT', 'UNSAT', 'UNK'])


class SAT:
    def __init__(self, cnffile, nvars, ncls, solver, phasesaving, timeout, tries):
        self.cnffile = cnffile
        self.nvars = nvars
        self.ncls = ncls
        self.solver = solver
        self.phasesaving = phasesaving
        self.timeout = timeout if timeout > 0 else None
        self.tries = tries

    def call(self, shuf):
        cat = 'cat' if not shuf else 'shuf'
        phase = '--forcephase=false' if self.phasesaving else '--phase=false --forcephase=true'
        proc = Popen(shlex.split(f'./{self.solver} -q --seed={random.randint(0, 1e9)} {phase}'), stdin=PIPE, stdout=PIPE, stderr=DEVNULL, text=True)
        proc.stdin.write(f'p cnf {self.nvars} {self.ncls}\n')
        proc.stdin.flush()
        Popen(shlex.split(f'{cat} {self.cnffile}'), stdout=proc.stdin).communicate()
        return proc

    def solve(self, shuf):
        attempt = 1
        while self.tries is None or attempt <= self.tries:
            proc = self.call(shuf)
            signal.signal(signal.SIGTERM, lambda x, y: kill(proc))
            start = time.time()
            try:
                out = proc.communicate(timeout=self.timeout)[0]
                if proc.returncode == 10:
                    result = Result.SAT
                    model = self.parsemodel(out)
                    break
                elif proc.returncode == 20:
                    result = Result.UNSAT
                    model = None
                    break
                else:
                    raise Exception(f'ERROR: Unknown return code: {proc.returncode}')
            except TimeoutExpired:
                proc.kill()
                proc.communicate()
                result = Result.UNK
                model = None
                attempt += 1
        elapsed = time.time() - start
        return result, model, attempt, elapsed

    def parsemodel(self, out):
        return [None] + [int(x) > 0 for x in re.split('\nv | ', out)[2:-1]]


def kill(proc):
    proc.kill()
    sys.exit()
