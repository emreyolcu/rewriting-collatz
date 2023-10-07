# Collatz-like problems as termination of rewriting
This repository accompanies the paper [*An automated approach to the Collatz conjecture*](https://www.cs.cmu.edu/~eyolcu/research/rewriting-collatz.pdf), published in the [Journal of Automated Reasoning](https://doi.org/10.1007/s10817-022-09658-8). It includes
- a minimal termination prover that implements the extended/weakly monotone Σ-algebra framework via natural, arctic, and tropical matrix interpretations,
- string rewriting systems that simulate the iterated applications of several Collatz-like functions,
- scripts to reproduce the automated proofs in the paper.

## Contents
- `prover/` includes the code for the termination prover.
- `rules/` includes the rewriting systems.
- `proofs/` includes the relative termination proofs.

## Rewriting systems
`rules/` contains the rewriting systems that appear in the paper. In order to ensure compatibility with other termination tools, the alphabets of the included systems use only ASCII characters. Therefore they use different symbols than the corresponding systems in the paper.

`relative/` contains the relative termination problems that several of the problems in the paper reduce to. These are used in producing the subparts of the termination proofs in the paper.

The included rewriting systems are in a nonstandard format. In particular, they use only single-letter symbols and do not contain spaces between symbols. (The command-line argument `--spaced` enables prover support for multi-letter symbols with spaces between them.) You may use the script `tpdb-convert.py` to convert them into the [TPDB format](https://www.lri.fr/~marche/tpdb/format.html) accepted by most termination tools. Example usage:
```
> cat rules/collatz-T.srs | ./tpdb-convert.py
(RULES
  a d -> d ,
  b d -> g d ,
  a e -> e a ,
  a f -> e b ,
  a g -> f a ,
  b e -> f b ,
  b f -> g a ,
  b g -> g b ,
  c e -> c b ,
  c f -> c a a ,
  c g -> c a b
)
```

## Instructions
*Requirements*: Python (v3.7+), NumPy (v1.19+), [CaDiCaL](https://github.com/arminbiere/cadical)

`./install-cadical.sh` downloads CaDiCaL, compiles it, and creates a symbolic link to the executable.

### Example run of the prover
```
> python prover/main.py rules/z086.srs -i natural -d 4 -rw 7 --printascii
Rewriting system:
  aa -> bc
  bb -> ac
  cc -> ab
CNF: 5544 variables, 45210 clauses (0.095 s)
Timeout: None
Workers: 4
SAT (Attempt 1, 0.114 s)

Natural: dimension 4, input width 7, result width 7
[a]: /1 3    \       /1\
     |       |       | |
     |  1   1| x  +  |1|
     \  1 2  /       \ /

[b]: /1     2\       / \
     |       |       | |
     |      1| x  +  | |
     \  1   2/       \2/

[c]: /1 1    \       /1\
     |      2|       | |
     |  1   1| x  +  |3|
     \  1    /       \ /

[aa]  >  [bc]: /1 3    \       /2\         /1 3    \       /1\
               |       |       | |         |       |       | |
               |  1 2  | x  +  |1|    >    |  1    | x  +  | |
               \  2   2/       \2/         \  2   2/       \2/

[bb]  >  [ac]: /1 2   6\       /4\         /1 1   6\       /2\
               |       |       | |         |       |       | |
               |  1   2| x  +  |2|    >    |  1   2| x  +  |1|
               \  2   4/       \6/         \  2   4/       \6/

[cc]  >  [ab]: /1 1   2\       /2\         /1     2\       /1\
               |  2    |       | |         |       |       | |
               |  1   2| x  +  |3|    >    |  1   2| x  +  |3|
               \      2/       \ /         \      2/       \ /

Relatively terminating rules:
  aa -> bc
  bb -> ac
  cc -> ab

QED
```

### Reproducing the proofs
- `./proofs.sh` finds the termination proofs that we refer to in the "Automated Proofs" section of the paper and writes them under the `proofs` directory.
- `./subsystems.py` finds the lowest-dimensional termination proofs for the subsytems of `collatz-T.srs` that we refer to in the "Subsets of T" section of the paper.
- `./negative-shuffle.py` runs the experiments concerning negative branching and clause shuffling that we refer to in the "SAT Solving Considerations" section of the paper.
