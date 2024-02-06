#!/usr/bin/python

from itertools import *
from more_itertools import powerset # python -m pip install more-itertools

from ast import *
import os

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("fp",type=str,help="path to file with settings")
parser.add_argument("rank",type=int,help="rank")
parser.add_argument("n",type=int,help="number of elements")
parser.add_argument("--solver", choices=['cadical', 'pycosat'], default='pycosat', help="SAT solver")
args = parser.parse_args()

def count(n,forb):
	from pysat.formula import IDPool,CNF
	vpool = IDPool()
	N = range(n)
	
	var_pair = {I:vpool.id(I) for I in combinations(N,rank)}

	cnf = CNF()

	for I in combinations(N,rank):
		cnf.append([-var_pair[I],+var_pair[I]]) # define variables to avoid issues when a variable is not used in any constraint

	for f in forb:
		for s in f:
			assert(s in ['+','-'])

	forb_sgn = [[(+1 if s == '+' else -1) for s in f] for f in forb]

	# signature functions: forbid invalid configuartions 
	for packet in combinations(N,rank+1):
		packet_r = list(combinations(packet,rank)) # lexicographically sorted r-tuples in packet
		assert(len(packet_r) == rank+1)
		for S in forb_sgn:
			assert(len(S) == rank+1)
			cnf.append([-S[j]*var_pair[packet_r[j]] for j in range(rank+1)])

	fp = "_tmp.cnf"
	cnf.to_file(fp)
	import subprocess
	result = subprocess.run(['KCBox','ExactMC','--quiet',fp], stdout=subprocess.PIPE)
	s = result.stdout
	ct = int(s.split()[-1])
	return ct

def disp(forb):
	return "Forb("+','.join(sorted(forb))+")"

def gen_url(seq):
	return "https://oeis.org/search?q="+"%2C".join(str(x) for x in seq)

rank = args.rank

types = {}
ct = 0
for line in open(args.fp):
	forb = literal_eval(line)
	ct += 1

	seq = []
	for n in range(rank,args.n+1):
		cnt = count(n,forb)
		if cnt == None: break
		seq.append(cnt)

	print("#",ct,":",disp(forb),"gives",seq,gen_url(seq))
	if tuple(seq) in types:
		print(30*"?"+"might be the same as",types[tuple(seq)],"??????")
	else:
		types[tuple(seq)] = (ct,forb)

