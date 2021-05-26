import sys
from itertools import product
import numpy as np

from encoder import Encoder
from decoder import Decoder


class ArcticEncoder(Encoder):
    def __init__(self, full, dimension, width, negwidth, removeany):
        super().__init__(full, dimension, width, removeany)
        self.negwidth = negwidth

    def less(self, x, y):
        self.add((-self.index((*x, self.width - 1)),))
        for i in range(1, self.width):
            self.add((-self.index((*x, i - 1)), self.index((*y, i))))

    def impliedless(self, x, y, z):
        self.add((-self.index(z), -self.index((*x, self.width - 1))))
        for i in range(1, self.width):
            self.add((-self.index(z), -self.index((*x, i - 1)), self.index((*y, i))))

    def sum(self, x, y, z=()):
        r = (('+', x, y),) if not z else z
        self.order(r)
        self.lessorequal(x, r)
        self.lessorequal(y, r)
        for i in range(self.width):
            self.add((self.index((*x, i)), self.index((*y, i)), -self.index((*r, i))))
        return r

    def product(self, x, y, z=()):
        r = (('x', x, y),) if not z else z
        self.order(r)
        self.add((self.index((*x, 0)), -self.index((*r, 0))))
        self.add((self.index((*y, 0)), -self.index((*r, 0))))
        for i in range(self.width):
            for j in range(self.width):
                s = i + j - self.negwidth
                if s > self.width - 1:
                    self.add((-self.index((*x, i)), -self.index((*y, j))))
                    break
                elif s < -1:
                    continue
                elif s == -1:
                    self.add((-self.index((*x, 0)), -self.index((*y, 0)), self.index((*x, i + 1)), self.index((*y, j + 1))))
                else:
                    self.add((-self.index((*x, i)), -self.index((*y, j)), self.index((*r, s))))
                    if s < self.width - 1:
                        if i < self.width - 1 and j < self.width - 1:
                            self.add((self.index((*x, i + 1)), self.index((*y, j + 1)), -self.index((*r, s + 1))))
                        elif i == self.width - 1:
                            self.add((-self.index((*x, i)), self.index((*y, j + 1)), -self.index((*r, s + 1))))
                        elif j == self.width - 1:
                            self.add((self.index((*x, i + 1)), -self.index((*y, j)), -self.index((*r, s + 1))))
        return r

    def weaklymonotone(self, s):
        self.add((self.index(('M', s, 0, 0, self.negwidth)), self.index(('v', s, 0, self.negwidth))))

    def concatenate(self, s, t):
        self.matrixmultiply(s, t)
        if not self.full:
            for i in range(self.dimension):
                pv = self.innerprod([('M', s, i, k) for k in range(self.dimension)],
                                    [('v', t, k) for k in range(self.dimension)])
                self.sum(pv, ('v', s, i), ('v', s + t, i))

    def relate(self, r):
        v = ('>', r.left, r.right) if r.strict and self.removeany else None
        def f(x, y):
            self.lessorequal(x, y)
            self.impliedless(x, y, v)
        if r.strict:
            if not self.removeany:
                rel = self.less
            else:
                rel = f
        else:
            rel = self.lessorequal
        for i in range(self.dimension):
            for j in range(self.dimension):
                rel(('M', r.right, i, j), ('M', r.left, i, j))
            if not self.full:
                rel(('v', r.right, i), ('v', r.left, i))
        if v is not None:
            return self.index(v)

    def limitinput(self, s, w):
        for i in range(self.dimension):
            for j in range(self.dimension):
                self.add((-self.index(('M', s, i, j, w)),))
            if not self.full:
                self.add((-self.index(('v', s, i, w)),))


class ArcticDecoder(Decoder):
    def __init__(self, full, symbols, index, dimension, width, negwidth, removeany, printascii):
        super().__init__(full, symbols, index, dimension, width, removeany, printascii)
        self.negwidth = negwidth

    def initinterp(self):
        M = np.empty((self.dimension, self.dimension), dtype=np.int64)
        v = np.empty(self.dimension, dtype=np.int64) if not self.full else None
        return M, v

    def multiply(self, L, R):
        LM, Lv = L
        RM, Rv = R
        d = LM.shape[0]
        Z = np.empty((d, d), dtype=np.int64)
        y = np.empty(d, dtype=np.int64) if (Lv is not None and Rv is not None) else None
        plus = lambda x, y: max(x, y)
        times = lambda x, y: (0 if x == 0 or y == 0 else x + y - 1) - self.negwidth
        for i in range(d):
            for j in range(d):
                s = 0
                for k in range(d):
                    s = plus(s, times(LM[i, k], RM[k, j]))
                Z[i, j] = s
        if y is not None:
            for i in range(d):
                s = 0
                for k in range(d):
                    s = plus(s, times(LM[i, k], Rv[k]))
                y[i] = plus(s, Lv[i])
        return Z, y

    def checkrel(self, r, interp):
        L = self.interpret(r.left, interp)
        R = self.interpret(r.right, interp)
        LM, Lv = L
        RM, Rv = R
        d = self.dimension
        ge = (all(LM[i, j] >= RM[i, j] for i, j in product(range(d), range(d))) and
              ((Lv is None or Rv is None) or all(Lv[i] >= Rv[i] for i in range(d))))
        if not ge:
            rl = Decoder.rlen(r)
            sys.exit('ERROR: Interpretation is not decreasing:\n' +
                     Decoder.rstr(r) + self.rule((L, R, None), rl - 1, pad=rl))
        greater = lambda x, y: x > y or x == 0 == y
        strict = (all(greater(LM[i, j], RM[i, j]) for i, j in product(range(d), range(d))) and
                  ((Lv is None or Rv is None) or all(greater(Lv[i], Rv[i]) for i in range(d))))
        return L, R, strict

    def val(self, x):
        l = len(str(self.width)) + int(self.negwidth > 0)
        return l * ' ' if x == 0 else f'{(x - self.negwidth - 1):{l}d}'

    def valtex(self, x):
        l = len(str(self.width)) + int(self.negwidth > 0)
        return '\cdot' if x == 0 else f'{(x - self.negwidth - 1):{l}d}'
