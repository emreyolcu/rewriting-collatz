#!/usr/bin/env python

import sys
import re
import argparse


def to_term(s, var):
    tmp = list(s) + [var]
    return '('.join(tmp) + ')' * (len(tmp) - 1)


def to_string(s, var):
    return ' '.join(s)


def parse(x, spaced):
    p = tuple(x.split()) if spaced else tuple(x)
    if not spaced and ' ' in p:
        sys.exit('ERROR: Alphabet cannot contain the space character')
    return p


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--type', '-t', type=str, default='string', choices=['string', 'term'])
    parser.add_argument('--var', '-v', type=str, default='x')
    parser.add_argument('--spaced', '-s', action='store_true')
    args = parser.parse_args()
    if args.type == 'string':
        convert = to_string
        end = ' ,\n'
    elif args.type == 'term':
        convert = to_term
        end = '\n'
    if args.type == 'term':
        print(f'(VAR {args.var})')
    lines = sys.stdin.readlines()
    if any(args.var in line for line in lines):
        sys.exit(f'ERROR: Variable "{args.var}" occurs as a function symbol')
    print('(RULES')
    last = len(lines) - 1
    for index, line in enumerate(lines):
        line = line.strip()
        if not line.startswith('//'):
            t = re.split(r'\s+([^ ]?->[^ ]?)\s+', line)
            print(' ', convert(parse(t[0], args.spaced), args.var), t[1], convert(parse(t[2], args.spaced), args.var), end=end if index < last else '\n')
    print(')')


if __name__ == '__main__':
    main()
