import sys
import fileinput
from collections import namedtuple
import re


def parse(x, spaced):
    p = tuple(x.split()) if spaced else tuple(x)
    if not spaced and ' ' in p:
        sys.exit('ERROR: Alphabet cannot contain the space character')
    return p


def join(x, spaced):
    return (' ' if spaced else '').join(x)


class Rule:
    def __init__(self, left, right, strict, top, spaced):
        self.spaced = spaced
        self.left = left
        self.right = right
        self.strict = strict
        self.top = top
        self.arrow = ('|' if self.top else '') + ('->' if self.strict else '->=')

    def __str__(self):
        return ' '.join([join(self.left, self.spaced), self.arrow, join(self.right, self.spaced)])

    def reverse(self):
        self.left = self.left[::-1]
        self.right = self.right[::-1]


class System:
    def __init__(self, symbols, rules, full, rev):
        self.symbols = symbols
        self.rules = rules
        self.full = full
        self.rev = rev

    def __str__(self):
        lines = []
        for r in self.rules:
            lines.append('  ' + str(r))
        return '\n'.join(lines)

    def reverserules(self):
        for r in self.rules:
            r.reverse()
        self.rev = not self.rev


def dp(system):
    if any(not r.strict for r in system.rules) or not system.full:
        sys.exit('ERROR: Dependency pairs can only be used for full termination')
    if ('#',) in system.symbols:
        sys.exit('ERROR: # is a reserved symbol when using dependency pairs')
    pairs = []
    defined = set()
    for r in system.rules:
        left = (r.left[0] + '#',) + r.left[1:]
        defined.add((left[0],))
        for i in range(len(r.right)):
            right = (r.right[i] + '#',) + r.right[(i + 1):]
            p = Rule(left, right, True, True, True)
            pairs.append(p)
            defined.add((right[0],))
    weakened = [Rule(r.left, r.right, False, False, True) for r in system.rules]
    return System(defined | system.symbols, pairs + weakened, False, system.rev)


def pad(left, right, pre, post, symbols, top):
    rules = [(left, right)]
    if pre:  rules = [(s + l, s + r) for (l, r) in rules for s in (([] if top else [('<',)]) + symbols)]
    if post: rules = [(l + s, r + s) for (l, r) in rules for s in (symbols + [('>',)])]
    return rules


def fold(st):
    return tuple('(' + st[i] + ',' + st[i + 1] + ')' for i in range(0, len(st) - 1))


def tile(system):
    reserved = {('<',), ('>',), (',',), ('(',), (')',)}
    if reserved & system.symbols:
        sys.exit(f'ERROR: {" ".join(x[0] for x in sorted(reserved))} are reserved symbols when tiling')
    symbols = set()
    rules = []
    for r in system.rules:
        padded = pad(r.left, r.right, not r.top, True, sorted(system.symbols), not system.full)
        for p in padded:
            t = Rule(fold(p[0]), fold(p[1]), r.strict, r.top, True)
            rules.append(t)
            symbols.update((x,) for x in (t.left + t.right))
    return System(symbols, rules, system.full, system.rev)


def parserules(file, spaced):
    symbols = set()
    rules = []
    full = True
    rev = False
    for line in fileinput.input(file):
        line = line.strip()
        if line.startswith('//'):
            continue
        t = re.split(r'\s+([^ ]?->[^ ]?)\s+', line)
        top = t[1][0] == '|'
        bot = t[1][-1] == '|'
        if top or bot:
            full = False
        if bot:
            rev = True
        if top and bot:
            sys.exit('ERROR: Rules cannot be restricted simultaneously to top and bottom')
        arrow = t[1][(1 if top else 0):(-1 if bot else len(t[1]))]
        if arrow == '->':
            strict = True
        elif arrow == '->=':
            strict = False
        else:
            sys.exit(f'ERROR: Unknown reduction arrow "{arrow}"')
        r = Rule(parse(t[0], spaced), parse(t[2], spaced), strict, top or bot, spaced)
        rules.append(r)
        symbols.update((x,) for x in (r.left + r.right))
    if not full and any(not r.top and r.strict for r in rules):
        sys.exit('ERROR: Nontop rules cannot be strict in top termination')
    system = System(symbols, rules, full, False)
    if rev:
        system.reverserules()
    return system
