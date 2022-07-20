import sys
from itertools import product
import numpy as np

from encoder import Encoder
from decoder import Decoder


class TropicalEncoder(Encoder):
    def __init__(self, full, dimension, width, removeany):
        super().__init__(full, dimension, width, removeany)

    def less(self, x, y):
        self.add((self.index((*y, 0)),))
        for i in range(1, self.width):
            self.add((-self.index((*x, i - 1)), self.index((*y, i))))

    def impliedless(self, x, y, z):
        self.add((-self.index(z), self.index((*y, 0))))
        for i in range(1, self.width):
            self.add((-self.index(z), -self.index((*x, i - 1)), self.index((*y, i))))

    def sum(self, x, y, z=()):
        r = (('+', x, y),) if not z else z
        self.order(r)
        self.lessorequal(r, x)
        self.lessorequal(r, y)
        for i in range(self.width):
            self.add((-self.index((*x, i)), -self.index((*y, i)), self.index((*r, i))))
        return r

    def product(self, x, y, z=()):
        r = (('x', x, y),) if not z else z
        self.order(r)
        self.add((-self.index((*x, self.width - 1)), self.index((*r, self.width - 1))))
        self.add((-self.index((*y, self.width - 1)), self.index((*r, self.width - 1))))
        for i in range(self.width):
            for j in range(self.width):
                s = i + j
                if s > self.width - 1:
                    self.add((self.index((*x, self.width - 1)), self.index((*y, self.width - 1)), -self.index((*x, i - 1)), -self.index((*y, j - 1))))
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

    def monotone(self, s):
        self.add((-self.index(('M', s, 0, 0, self.width - 1)),))

    def weaklymonotone(self, s):
        self.add((-self.index(('M', s, 0, 0, self.width - 1)), -self.index(('v', s, 0, self.width - 1))))

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
                self.add((-self.index(('M', s, i, j, w - 1)), self.index('M', s, i, j, self.width - 1)))
            if not self.full:
                self.add((-self.index(('v', s, i, w - 1)), self.index('v', s, i, self.width - 1)))

    def marktop(self, s):
        for i in range(1, self.dimension):
            for j in range(self.dimension):
                self.add((self.index(('M', s, i, j, self.width - 1)),))
            self.add((self.index(('v', s, i, self.width - 1)),))

    def markbot(self, s):
        for i in range(self.dimension):
            for j in range(self.dimension):
                self.add((self.index(('M', s, i, j, self.width - 1)),))


class TropicalDecoder(Decoder):
    def positive(self, x):
        return x < self.width

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
        plus = lambda x, y: min(x, y)
        times = lambda x, y: (self.width if x == self.width or y == self.width else x + y)
        for i in range(d):
            for j in range(d):
                s = self.width
                for k in range(d):
                    s = plus(s, times(LM[i, k], RM[k, j]))
                Z[i, j] = s
        if y is not None:
            for i in range(d):
                s = self.width
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
        greater = lambda x, y: x > y or x == self.width == y
        strict = (all(greater(LM[i, j], RM[i, j]) for i, j in product(range(d), range(d))) and
                  ((Lv is None or Rv is None) or all(greater(Lv[i], Rv[i]) for i in range(d))))
        return L, R, strict

    def val(self, x):
        l = len(str(self.width))
        return l * ' ' if x == self.width else f'{x:{l}d}'

    def valtex(self, x):
        l = len(str(self.width))
        return '\cdot' if x == self.width else f'{x:{l}d}'
