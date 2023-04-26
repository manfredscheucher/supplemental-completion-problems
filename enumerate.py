# description: sat program to enumerate partial generalized signotopes 
# author: manfred scheucher 2023

from basics import *


import argparse
parser = argparse.ArgumentParser()
parser.add_argument("fp",type=str,help="file with list of settings")
parser.add_argument("n",type=int,help="number of elements")
parser.add_argument("--freezeros","-fz",action="store_true",help="assume every zero is free, i.e., can be set to true and false")
parser.add_argument("--nozeros","-nz",action="store_true",help="assume no zeros")
parser.add_argument("--countonly","-co",action="store_true",help="only count/do not print configurations")
parser.add_argument("--table","-t",action="store_true",help="list how many configurations have exactly z zeros")
parser.add_argument("--fp_dup",type=str,help="write possibly_duplicates to file")

args = parser.parse_args()
vargs = vars(args)
print("c\tactive args:",{x:vargs[x] for x in vargs if vargs[x] != None and vargs[x] != False})




sequences = {}

possibly_duplicates = set()

ct0 = 0
for line in (open(args.fp).readlines()):
	ct0 += 1
	forbidden_patterns4_orig = literal_eval(line)

	if not args.countonly:
		print("#",ct0,":",forbidden_patterns4_orig)


	forbidden_patterns4 = forbidden_patterns_closure(forbidden_patterns4_orig)
	#print("closure of forbidden_patterns4:",len(forbidden_patterns4),forbidden_patterns4)

	if args.freezeros:
		forbidden_patterns4 = forbidden_patterns_filter_free_closure(forbidden_patterns4)
		#print("free-closure of forbidden_patterns4:",len(forbidden_patterns4),forbidden_patterns4)
		assert(forbidden_patterns4 == forbidden_patterns_closure(forbidden_patterns4))


	sequence = []
	for n in range(3,args.n+1):
		N = range(n)
		if not args.table:
			ct = 0
			for X in enum_partial(N,forbidden_patterns4,nozeros=args.nozeros):
				ct += 1
				if not args.countonly:
					X_str = X_to_str(X,N)
					print("solution",ct,":",X_str)
			sequence.append(ct)
		else:
			for z in range(0,n*(n-1)*(n-2)//6+1):
				ct = 0
				for X in enum_partial(N,forbidden_patterns4,nozeros=args.nozeros,num_zeros_max=z,num_zeros_min=z):
					ct += 1
					if not args.countonly:
						X_str = X_to_str(X,N)
						print("solution",ct,":",X_str)
				sequence.append(ct)


	print("#",ct0,":",forbidden_patterns4_orig,":",sequence)

	sequence = tuple(sequence)
	if sequence in sequences:
		print("seems to coincide with:",sequences[sequence])
		possibly_duplicates.add(sequences[sequence][1])
		possibly_duplicates.add(line)
	else:
		sequences[sequence] = (ct0,line)


print("=> (at least)",len(sequences),"distinct sequences")

if possibly_duplicates and args.fp_dup:
	print("write possibly_duplicates written to file",args.fp_dup)
	f = open(args.fp_dup,"w")
	for l in possibly_duplicates: f.write(l)