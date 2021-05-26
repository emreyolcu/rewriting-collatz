import sys
from abc import ABC
import numpy as np

from rules import join


class Decoder(ABC):
    def __init__(self, full, symbols, index, dimension, width, removeany, printascii):
        self.full = full
        self.symbols = symbols
        self.index = index
        self.dimension = dimension
        self.width = width
        self.removeany = removeany
        self.bracket = self.asciibrk if printascii else self.unicodebrk

    def parseinterp(self, model):
        interp = {}
        for s in self.symbols:
            M, v = self.initinterp()
            for i in range(self.dimension):
                for j in range(self.dimension):
                    M[i, j] = self.decode_coeff(('M', s, i, j), model)
                    if v is not None:
                        v[i] = self.decode_coeff(('v', s, i), model)
                    interp[s] = (M, v)
            if self.full and M[0, 0] <= 0:
                sl = Decoder.slen(s)
                sys.exit('ERROR: Interpretation is not monotone:\n' +
                         Decoder.sstr(s) + self.symbol((M, v), sl - 1, pad=sl))
        return interp

    def decode_coeff(self, coeff, model):
        for n in range(self.width):
            if not model[self.index[(*coeff, n)]]:
                return n
        else:
            return self.width

    def interpret(self, st, interp):
        W = interp[(st[0],)]
        for i in range(1, len(st)):
            W = self.multiply(W, interp[(st[i],)])
        return W

    def check(self, system, interp):
        removable = []
        for r in system.rules:
            C = self.checkrel(r, interp)
            interp[r] = C
            if C[2] and (system.full or r.top):
                removable.append(r)
        return removable

    def printsymbols(self, symbols, interp, file=sys.stdout):
        sl = {s: Decoder.slen(s) for s in symbols}
        pad = max(sl.values())
        for s in sorted(symbols):
            item = Decoder.sstr(s)
            print(item, end='', file=file)
            print(self.symbol(interp[s], sl[s] - 1, pad=pad), end='\n\n', file=file)

    def printsymbolstex(self, symbols, interp, file=sys.stdout):
        for s in sorted(symbols):
            item = f'[{s[0]}](\\vec{{x}}) ='
            print(item, file=file)
            print(self.interptex(interp[s]), end='\n\n', file=file)

    def printrules(self, rules, interp, file=sys.stdout):
        rl = {r: Decoder.rlen(r, self.rel(interp[r][2])) for r in rules}
        pad = max(rl.values())
        for r in rules:
            item = Decoder.rstr(r, self.rel(interp[r][2]))
            print(item, end='', file=file)
            print(self.rule(interp[r], rl[r] - 1, pad=pad), end='\n\n', file=file)

    def printrulestex(self, rules, interp, file=sys.stdout):
        for r in rules:
            iteml = f'[{join(r.left, r.spaced)}](\\vec{{x}}) ='
            itemr = f'= [{join(r.right, r.spaced)}](\\vec{{x}})'
            print(iteml, file=file)
            print(self.interptex(interp[r][0]), end='\n', file=file)
            print('>' if interp[r][2] else '\gtrsim', end='\n', file=file)
            print(self.interptex(interp[r][1]), end='\n', file=file)
            print(itemr, end='\n\n', file=file)

    def printtest(self, st, interp, spaced, file=sys.stdout):
        item = f'[{join(st, spaced)}]:'
        print(item, end='', file=file)
        print(self.symbol(self.interpret(st, interp), 0), end='\n\n', file=file)

    def symbol(self, I, sl, pad=0):
        M, v = I
        lines = []
        if pad == 0:
            lines.append('')
        for i in range(self.dimension):
            s = []
            s.append(self.pad(pad, sl, i))
            s.append(self.wrap(' '.join(self.val(M[i, j]) for j in range(self.dimension)), i))
            s.append(self.put(' x', i))
            if v is not None:
                s.append(self.sep(' + ', i))
                s.append(self.wrap(self.val(v[i]), i))
            lines.append(''.join(s))
        return '\n'.join(lines)

    def interptex(self, I):
        M, v = I
        lines = []
        lines.append(self.matrixtex(M))
        if v is None:
            lines.append('\\vec{x}')
        else:
            lines.append('\\vec{x} +')
            lines.append(self.matrixtex(np.expand_dims(v, axis=1)))
        return '\n'.join(lines)

    def matrixtex(self, M):
        r, c = M.shape
        lines = []
        lines.append('\\begin{bmatrix}')
        for i in range(r):
            lines.append('  ' + ' & '.join(self.valtex(M[i, j]) for j in range(c)) + (' \\\\' if i < r - 1 else ''))
        lines.append('\\end{bmatrix}')
        return '\n'.join(lines)

    def rule(self, I, sl, pad=0):
        LM, Lv = I[0]
        RM, Rv = I[1]
        strict = I[2]
        lines = []
        if pad == 0:
            lines.append('')
        for i in range(self.dimension):
            s = []
            s.append(self.pad(pad, sl, i))
            s.append(self.wrap(' '.join(self.val(LM[i, j]) for j in range(self.dimension)), i))
            s.append(self.put(' x', i))
            if Lv is not None:
                s.append(self.sep(' + ', i))
                s.append(self.wrap(self.val(Lv[i]), i))
            s.append(self.sep(f'  {self.rel(strict)}  ', i))
            s.append(self.wrap(' '.join(self.val(RM[i, j]) for j in range(self.dimension)), i))
            s.append(self.put(' x', i))
            if Rv is not None:
                s.append(self.sep(' + ', i))
                s.append(self.wrap(self.val(Rv[i]), i))
            lines.append(''.join(s))
        return '\n'.join(lines)

    def sstr(s):
        return f'[{s[0]}]:'

    def slen(s):
        return len(Decoder.sstr(s)) + 1

    def rstr(r, rel):
        return ' '.join([f'[{join(r.left, r.spaced)}]', rel, f'[{join(r.right, r.spaced)}]:'])

    def rlen(r, rel):
        return len(Decoder.rstr(r, rel)) + 1

    def pad(self, n, sl, i):
        if n == 0:
            return ' '
        return (n - sl) * ' ' if i == 0 else n * ' '

    def unicodebrk(self, i):
        if self.dimension == 1:
            return ('🮤', '🮥')
        else:
            if i == 0:
                return ('🭽', '🭾')
            elif i == self.dimension - 1:
                return ('🭼', '🭿')
            else:
                return ('▏', '▕')

    def asciibrk(self, i):
        if self.dimension == 1:
            return ('[', ']')
        else:
            if i == 0:
                return ('/', '\\')
            elif i == self.dimension - 1:
                return ('\\', '/')
            else:
                return ('|', '|')

    def put(self, s, i):
        return s if i == self.dimension // 2 else len(s) * ' '

    def sep(self, s, i):
        return ' ' + (s if i == self.dimension // 2 else len(s) * ' ') + ' '

    def wrap(self, s, i):
        b = self.bracket(i)
        return b[0] + s + b[1]

    def rel(self, strict):
        if strict is None:
            rel = '≱'
        else:
            rel = '>' if strict else '≥'
        return rel
