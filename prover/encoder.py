import sys
from abc import ABC
from collections import defaultdict


class Encoder(ABC):
    def __init__(self, full, dimension, width, removeany):
        self.clauses = []
        self.variables = {}
        self.full = full
        self.dimension = dimension
        self.width = width
        self.removeany = removeany

    def __str__(self):
        return f'CNF: {len(self.variables)} variables, {len(self.clauses)} clauses'

    def dimacs(self, header=True, file=sys.stdout):
        if header:
            nv, nc = len(self.variables), len(self.clauses)
            print(f'p cnf {nv} {nc}', file=file)
        for c in self.clauses:
            print(' '.join(str(l) for l in c), '0', file=file)

    def index(self, l):
        return self.variables.setdefault(l, len(self.variables) + 1)

    def add(self, literals):
        self.clauses.append(tuple(literals))

    def order(self, x):
        for i in range(self.width - 1):
            self.add((self.index((*x, i)), -self.index((*x, i + 1))))

    def lessorequal(self, x, y):
        for i in range(self.width):
            self.add((-self.index((*x, i)), self.index((*y, i))))

    def monotone(self, s):
        self.add((self.index(('M', s, 0, 0, 0)),))

    def ksum(self, xs, z=()):
        r = xs[0]
        for i in range(1, len(xs)):
            r = self.sum(r, xs[i], z if i == len(xs) - 1 else ())
        return r

    def innerprod(self, xs, ys, z=()):
        pvs = []
        for x, y in zip(xs, ys):
            pvs.append(self.product(x, y))
        return self.ksum(pvs, z)

    def matrixmultiply(self, s, t):
        if self.dimension == 1:
            self.product(('M', s, 0, 0), ('M', t, 0, 0), ('M', s + t, 0, 0))
        else:
            for i in range(self.dimension):
                for j in range(self.dimension):
                    self.innerprod([('M', s, i, k) for k in range(self.dimension)],
                                   [('M', t, k, j) for k in range(self.dimension)],
                                   ('M', s + t, i, j))
