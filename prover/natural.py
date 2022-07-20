import sys
from itertools import product
import numpy as np

from encoder import Encoder
from decoder import Decoder


class NaturalEncoder(Encoder):
    def less(self, x, y):
        self.add((-self.index((*x, self.width - 1)),))
        self.add(( self.index((*y, 0)),))
        for i in range(1, self.width):
            self.add((-self.index((*x, i - 1)), self.index((*y, i))))

    def impliedless(self, x, y, z):
        self.add((-self.index(z), -self.index((*x, self.width - 1))))
        self.add((-self.index(z), self.index((*y, 0))))
        for i in range(1, self.width):
            self.add((-self.index(z), -self.index((*x, i - 1)), self.index((*y, i))))

    def sum(self, x, y, z=()):
        r = (('+', x, y),) if not z else z
        self.order(r)
        self.lessorequal(x, r)
        self.lessorequal(y, r)
        for i in range(self.width + 1):
            for j in range(self.width + 1):
                s = i + j
                if s > self.width:
                    self.add((-self.index((*x, i - 1)), -self.index((*y, j - 1))))
                    break
                else:
                    if s != 0:
                        c = []
                        if i != 0: c.append(-self.index((*x, i - 1)))
                        if j != 0: c.append(-self.index((*y, j - 1)))
                        c.append(self.index((*r, s - 1)))
                        self.add(c)
                    if s != self.width:
                        self.add((self.index((*x, i)), self.index((*y, j)), -self.index((*r, s))))
        return r

    def product(self, x, y, z=()):
        r = (('x', x, y),) if not z else z
        self.order(r)
        self.add((self.index((*x, 0)), -self.index((*r, 0))))
        self.add((self.index((*y, 0)), -self.index((*r, 0))))
        for i in range(1, self.width + 1):
            for j in range(1, self.width + 1):
                p = i * j
                if p > self.width:
                    self.add((-self.index((*x, i - 1)), -self.index((*y, j - 1))))
                    break
                else:
                    self.add((-self.index((*x, i - 1)), -self.index((*y, j - 1)), self.index((*r, p - 1))))
                    if p < self.width:
                        self.add((self.index((*x, i)), self.index((*y, j)), -self.index((*r, p))))
        return r

    def monotone(self, s):
        self.add((self.index(('M', s, 0, 0, 0)),))

    def concatenate(self, s, t):
        self.matrixmultiply(s, t)
        for i in range(self.dimension):
            pv = self.innerprod([('M', s, i, k) for k in range(self.dimension)],
                                [('v', t, k) for k in range(self.dimension)])
            self.sum(pv, ('v', s, i), ('v', s + t, i))

    def relate(self, r):
        v = ('>', r.left, r.right) if r.strict and self.removeany else None
        for i in range(self.dimension):
            for j in range(self.dimension):
                self.lessorequal(('M', r.right, i, j), ('M', r.left, i, j))
            if r.strict and i == 0:
                if not self.removeany:
                    self.less(('v', r.right, i), ('v', r.left, i))
                else:
                    self.lessorequal(('v', r.right, i), ('v', r.left, i))
                    self.impliedless(('v', r.right, i), ('v', r.left, i), v)
            else:
                self.lessorequal(('v', r.right, i), ('v', r.left, i))
        if v is not None:
            return self.index(v)

    def limitinput(self, s, w):
        for i in range(self.dimension):
            for j in range(self.dimension):
                self.add((-self.index(('M', s, i, j, w)),))
            self.add((-self.index(('v', s, i, w)),))

    def marktop(self, s):
        for i in range(1, self.dimension):
            for j in range(self.dimension):
                self.add((-self.index(('M', s, i, j, 0)),))
            self.add((-self.index(('v', s, i, 0)),))

    def markbot(self, s):
        for i in range(self.dimension):
            for j in range(self.dimension):
                self.add((-self.index(('M', s, i, j, 0)),))


class NaturalDecoder(Decoder):
    def positive(self, x):
        return x > 0

    def initinterp(self):
        M = np.empty((self.dimension, self.dimension), dtype=np.int64)
        v = np.empty(self.dimension, dtype=np.int64)
        return M, v

    def multiply(self, L, R):
        return (L[0] @ R[0], L[0] @ R[1] + L[1])

    def checkrel(self, r, interp):
        L = self.interpret(r.left, interp)
        R = self.interpret(r.right, interp)
        LM, Lv = L
        RM, Rv = R
        d = self.dimension
        ge = (all(LM[i, j] >= RM[i, j] for i, j in product(range(d), range(d))) and
              all(Lv[i]    >= Rv[i]    for i in range(d)))
        if not ge:
            rl = Decoder.rlen(r)
            sys.exit('ERROR: Interpretation is not decreasing:\n' +
                     Decoder.rstr(r) + self.rule((L, R, None), rl - 1, pad=rl))
        strict = Lv[0] > Rv[0]
        return L, R, strict

    def val(self, x):
        l = len(str(self.width))
        return l * ' ' if x == 0 else f'{x:{l}d}'

    def valtex(self, x):
        l = len(str(self.width))
        return '\cdot' if x == 0 else f'{x:{l}d}'
