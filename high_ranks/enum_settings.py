from itertools import *
from more_itertools import powerset


import argparse
parser = argparse.ArgumentParser()
parser.add_argument("rank",type=int,help="rank")
args = parser.parse_args()

rank = args.rank

potential = [P for P in [''.join(P) for P in product('+-',repeat=rank+1)] if P.count('++') == 0]

found = []

for setting in powerset(potential):
	setting = list(sorted(setting))

	lexmin = setting[:]
	for reflection in [0,1]:
		for negation in [0,1]:
			setting2 = setting[:]
			if reflection:
				setting2 = [pattern[::-1] for pattern in setting2]
			if negation:
				setting2 = [''.join(('+' if c == '-' else '-') for c in pattern) for pattern in setting2]
			
			#print("setting2",setting2)
			setting2 = list(sorted(setting2))
			if set(setting2).issubset(potential) and setting2 < lexmin:
				lexmin = setting2[:]

	if lexmin not in found:
		print(lexmin)
		found.append(lexmin)
	
#print("ct",len(found))
