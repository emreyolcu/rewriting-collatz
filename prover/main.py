import sys
import argparse
import time
import os
import tempfile
import atexit
from multiprocessing import Pool
import signal

import rules
from rules import parse, join
from matrix import MatrixEncoder, MatrixDecoder
from arctic import ArcticEncoder, ArcticDecoder
from sat import SAT, Result


signal.signal(signal.SIGINT, lambda x, y: sys.exit(0))


def encode(system, args):
    if args.interpretation == 'matrix':
        if args.negwidth > 0:
            sys.exit('ERROR: Matrix interpretations can only use natural numbers')
        E = MatrixEncoder(system.full, args.dimension, args.resultwidth, args.removeany)
    elif args.interpretation == 'arctic':
        if system.full and args.negwidth > 0:
            sys.exit('ERROR: Arctic interpretations can only use natural numbers in full termination')
        E = ArcticEncoder(system.full, args.dimension, args.resultwidth, args.negwidth, args.removeany)

    # Order
    for s in system.symbols:
        for i in range(args.dimension):
            for j in range(args.dimension):
                E.order(('M', s, i, j))
            if isinstance(E, MatrixEncoder) or not E.full:
                E.order(('v', s, i))

    # Monotonicity
    if E.full:
        for s in system.symbols:
            E.monotone(s)
    else:
        if isinstance(E, ArcticEncoder):
            for s in system.symbols:
                E.weaklymonotone(s)

    # Input width
    if args.inputwidth is not None and args.inputwidth < args.resultwidth:
        for s in system.symbols:
            E.limitinput(s, args.inputwidth)

    # Rule interpretations
    parts = set()
    for r in system.rules:
        for st in (r.left, r.right):
            p = (st[0],)
            for i in range(1, len(st)):
                q = (st[i],)
                pn = p + q
                if pn not in parts:
                    E.concatenate(p, q)
                    parts.add(pn)
                p = pn

    # Inequalities
    aux = []
    for r in system.rules:
        v = E.relate(r)
        if v is not None:
            aux.append(v)
    if aux:
        E.add(aux)

    # Marked symbols
    if args.markedsymbols:
        if not isinstance(E, MatrixEncoder):
            sys.exit('ERROR: Marked symbols can only be used with matrix interpretations')
        else:
            args.markedsymbols = [(s,) for s in args.markedsymbols]
            for s in args.markedsymbols:
                for i in range(1, args.dimension):
                    for j in range(args.dimension):
                        E.add((-E.index(('M', s, i, j, 0)),))
                    E.add((-E.index(('v', s, i, 0)),))

    # # [c](x) = v and [d](x) = Mx
    # for i in range(args.dimension):
    #     for j in range(args.dimension):
    #         E.add((-E.index(('M', ('c',), i, j, 0)),))
    #     E.add((-E.index(('v', ('d',), i, 0)),))
    #     # # [ternary](x) = Mx
    #     # E.add((-E.index(('v', ('e',), i, 0)),))
    #     # E.add((-E.index(('v', ('f',), i, 0)),))
    #     # E.add((-E.index(('v', ('g',), i, 0)),))

    return E


def decode(system, E, model, args):
    if args.interpretation == 'matrix':
        D = MatrixDecoder(E.full, system.symbols, E.variables, args.dimension, args.resultwidth, args.removeany, args.printascii)
    elif args.interpretation == 'arctic':
        D = ArcticDecoder(E.full, system.symbols, E.variables, args.dimension, args.resultwidth, args.negwidth, args.removeany, args.printascii)

    iw = args.resultwidth if args.inputwidth is None else min(args.resultwidth, args.inputwidth)
    print(f'\n{args.interpretation.capitalize()}: dimension {args.dimension}, input width {iw + 1}, result width {args.resultwidth + 1}' + (f', negative width {args.negwidth}' if args.negwidth > 0 else ''))

    interp = D.parseinterp(model)
    removable = D.check(system, interp)

    if not args.no_print:
        D.printsymbols(system.symbols, interp)
        D.printrules(system.rules, interp)

    if args.printtex:
        print('\nTeX:', file=sys.stderr)
        D.printsymbolstex(system.symbols, interp, file=sys.stderr)
        D.printrulestex(system.rules, interp, file=sys.stderr)

    print(f'Relatively {"" if system.full else "top-"}terminating rules:', file=sys.stderr)
    for r in removable:
        print(f'  {join(r.left, r.spaced)} -> {join(r.right, r.spaced)}', file=sys.stderr)
        system.rules.remove(r)

    system.symbols = set((x,) for xs in ((r.left + r.right) for r in system.rules) for x in xs)

    if any(rule.strict for rule in system.rules):
        print('\nRemaining strict rules:', file=sys.stderr)
        for r in system.rules:
            if r.strict:
                print(f'  {join(r.left, r.spaced)} {r.arrow} {join(r.right, r.spaced)}', file=sys.stderr)
        if args.outfile:
            writeout(system, args.outfile)
        code = 11
    else:
        print('\nQED', file=sys.stderr)
        code = 19

    if args.testfile:
        with open(args.testfile) as f:
            print('\nTest:', file=sys.stderr)
            for line in f.read().splitlines():
                st = parse(line.strip(), args.spaced)
                diff = list(set(st) - set(s[0] for s in system.symbols))
                if diff:
                    sys.exit(f'ERROR: Test string contains unknown symbols: {diff}')
                D.printtest(st, interp, args.spaced, file=sys.stderr)

    return code


def writeout(system, outfile):
    with open(outfile, 'w') as f:
        for r in system.rules:
            print(f'{join(r.left, r.spaced)} {r.arrow} {join(r.right, r.spaced)}', file=f)


def parseargs():
    parser = argparse.ArgumentParser()

    parser.add_argument('rulefile', type=str)
    parser.add_argument('--reverserules',    '-rev',  action='store_true')
    parser.add_argument('--dependencypairs', '-dp',   action='store_true')
    parser.add_argument('--tilerules',       '-tile', action='store_true')
    parser.add_argument('--removeany',       '-any',  action='store_true')
    parser.add_argument('--spaced',          '-spc',  action='store_true')
    parser.add_argument('--markedsymbols',   '-mark', nargs='+')
    parser.add_argument('--testfile',        '-test', type=str)
    parser.add_argument('--outfile',         '-out',  type=str)

    parser.add_argument('--interpretation',  '-i',  type=str, default='matrix', choices=['matrix', 'arctic'])
    parser.add_argument('--dimension',       '-d',  type=int, default=3)
    parser.add_argument('--inputwidth',      '-iw', type=int)
    parser.add_argument('--resultwidth',     '-rw', type=int, default=4)
    parser.add_argument('--negwidth',        '-nw', type=int, default=0)
    parser.add_argument('--printcnf',        '-p',  action='store_true')

    parser.add_argument('--cnffile',         '-cnf',   type=str)
    parser.add_argument('--solver',          '-sol',   type=str, default='cadical', choices=['cadical'])
    parser.add_argument('--phasesaving',     '-phase', action='store_true')
    parser.add_argument('--timeout',         '-tout',  type=int, default=0)
    parser.add_argument('--workers' ,        '-work',  type=int, default=4)
    parser.add_argument('--tries',           '-try',   type=int)
    parser.add_argument('--run-once',        '-once',   action='store_true')
    parser.add_argument('--no-shuffle',      '-noshuf', action='store_true')
    parser.add_argument('--no-print',        '-np',     action='store_true')
    parser.add_argument('--printascii',      '-asc',    action='store_true')
    parser.add_argument('--printtex',        '-tex',    action='store_true')

    args = parser.parse_args()
    return args


def cleanup(files):
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    for f in files:
        try:
            os.remove(f)
        except OSError:
            pass


def main():
    args = parseargs()
    if args.inputwidth:
        args.inputwidth -= 1
    if args.resultwidth < 2:
        sys.exit('ERROR: Result width should be at least 2')
    args.resultwidth -= 1
    code = 0

    # Read rewriting system
    system = rules.parserules(args.rulefile, args.spaced)
    transform = []
    if args.reverserules:
        if system.rev:
            sys.exit('ERROR: System is already reversed for top termination')
        system.reverserules()

    if system.rev:
        transform.append('reversed')

    if args.dependencypairs:
        system = rules.dp(system)
        transform.append('dependency pairs')

    if args.tilerules:
        system = rules.tile(system)
        transform.append('tiled')

    print(f'Rewriting system{(" (" + (" & ").join(transform) + ")") if transform else ""}:')
    print(system, file=sys.stderr)

    cnfs = []
    atexit.register(lambda: cleanup(cnfs))

    result = Result.UNK

    while any(rule.strict for rule in system.rules) and not result == Result.UNSAT:
        # Encode constraints as CNF
        start = time.time()
        E = encode(system, args)
        elapsed = time.time() - start
        print(E, f'({elapsed:.3f} s)', file=sys.stderr)

        if args.printcnf:
            E.dimacs()
            sys.exit()

        # Write CNF to file
        if args.cnffile:
            cnffile = args.cnffile
            f = open(args.cnffile, 'w')
        else:
            os.makedirs('tmp', exist_ok=True)
            fd, cnffile = tempfile.mkstemp(dir='tmp')
            cnfs.append(cnffile)
            f = os.fdopen(fd, 'w')
        E.dimacs(header=False, file=f)
        f.close()

        # Try to solve CNF
        S = SAT(cnffile, len(E.variables), len(E.clauses), args.solver, args.phasesaving, args.timeout, args.tries)

        with Pool(processes=args.workers) as pool:
            shufs = ((args.workers == 1 or i != 0) and not args.no_shuffle for i in range(args.workers))
            r = pool.imap_unordered(S.solve, shufs)
            while True:
                try:
                    result, model, attempt, elapsed = r.next()
                    if result == Result.SAT:
                        print(f'SAT (Attempt {attempt}, {elapsed:.3f} s)', file=sys.stderr)
                        code = decode(system, E, model, args)
                    elif result == Result.UNSAT:
                        print(f'UNSAT ({elapsed:.3f} s)', file=sys.stderr)
                        code = 29
                    break
                except Exception as e:
                    sys.exit(e)

        if args.run_once:
            break

    sys.exit(code)


if __name__ == '__main__':
    main()
