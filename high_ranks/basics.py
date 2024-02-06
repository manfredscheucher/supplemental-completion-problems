from itertools import *
from ast import *
from sys import *
from copy import *
from pysat.formula import IDPool
import time
import os.path

USE_CADICAL = 0 # Manfred: you may set to 1 but make sure that you have installed the current version of pysat (an old version had a memory leak) 

if USE_CADICAL:
	from pysat.solvers import *
	SOLVER = "cadical"
else:
	import pycosat
	SOLVER = "pycosat"


def X_to_str(rank,X,N):
	return ''.join(X[I] for I in combinations(N,rank))


def X_from_str(rank,s,N):
	assert(len(list(combinations(N,rank))) == len(s))
	return {I: s[i] for i,I in enumerate(combinations(N,rank))}



def load_certificate(certificates_path,forbidden_patterns):
	forbidden_patternsstr = ','.join(sorted(forbidden_patterns))
	fp = f"{certificates_path}{forbidden_patternsstr}.txt"
	if not os.path.exists(fp):
		print(f"fp {fp} not exists")
		return None
	print("## load certificate from "+fp)
	cert = literal_eval(open(fp).readline())
	assert(cert['fpatterns'] == forbidden_patterns)
	return cert


def create_certificate(certificates_path,cert):
	if not os.path.exists(certificates_path): os.makedirs(certificates_path)
	forbidden_patternsstr = ','.join(sorted(cert['fpatterns']))
	fp = f"{certificates_path}{forbidden_patternsstr}.txt"
	#asforbidden_patternssert(not os.path.exists(fp)) # do not overwrite existing certificates
	with open(fp,"w") as f:
		f.write(str(cert)+"\n")
	print("## wrote certificate to "+fp)



CNF_cached = {}

def forbidden_patterns_closure(rank,forbidden_patterns):
	solution_patterns = [list(pattern) for pattern in product(['+','-'],repeat=rank+1) if ''.join(pattern) not in forbidden_patterns]

	closure = set(forbidden_patterns)
	for pattern in product(['+','-','?'],repeat=rank+1):
		pattern = ''.join(pattern)
		completable = False
		for sol in solution_patterns:
			if not [i for i in range(rank+1) if pattern[i] != '?' and pattern[i] != sol[i]]:
				completable = True
		if not completable:
			closure.add(pattern)
	return closure


def forbidden_patterns_filter_free_closure(rank,forbidden_patterns):
	solution_patterns = [list(pattern) for pattern in product(['+','-'],repeat=rank+1) if ''.join(pattern) not in forbidden_patterns]

	closure = set(forbidden_patterns)
	for pattern in product(['+','-','?'],repeat=rank+1):
		pattern = ''.join(pattern)
		completable = False
		for sol in solution_patterns:
			if not [i for i in range(rank+1) if pattern[i] != '?' and pattern[i] != sol[i]]:
				completable = True

		# every zero must be completable to both, plus and minus
		all_zeros_free = True
		for k in range(rank+1):
			if pattern[k] == '?':
				for s in ['+','-']:
					pattern_fill = pattern[:k]+s+pattern[k+1:]
					completable_fill = False
					for sol in solution_patterns:
						if not [i for i in range(rank+1) if pattern_fill[i] != '?' and pattern_fill[i] != sol[i]]:
							completable_fill = True
					if not completable_fill:
						all_zeros_free = False

		if not completable or not all_zeros_free:
			closure.add(pattern)

	return closure

	
def test_completable(rank,X,N,forbidden_patterns,verify=False):
	X_nonzero = {I:X[I] for I in X if X[I] != '?'}
	for sol in enum_partial(rank,N,forbidden_patterns,nozeros=True,pre_set=X_nonzero,verify=verify):
		return True
	return False



def enum_partial(rank,N,forbidden_patterns,nozeros=False,DEBUG=False,pre_set={},
		num_zeros_max=None,num_zeros_min=None,blacklist_upset=[],blacklist_downset=[],verify=False):


	vpool = IDPool(start_from=1) 
	all_variables = {}

	# initialize variables
	for I in combinations(N,rank):
		for s in ['+','-','?']:
			all_variables[('trip',(*I,s))] = vpool.id()

	if num_zeros_max != None or num_zeros_min != None:
		maxnumzeros = len(list(combinations(N,rank)))
		for I in combinations(N,rank):
			for k in range(maxnumzeros+1):
				all_variables[('numzeros',(*I,k))] = vpool.id()


	def var(L):	return all_variables[L]
	def var_trip(*L): return var(('trip',L))
	def var_numzeros(*L): return var(('numzeros',L))


	global CNF_cached	

	forbidden_patternsstr = ','.join(sorted(forbidden_patterns))
	if (N,forbidden_patternsstr,nozeros) not in CNF_cached:

		constraints0 = []

		if DEBUG>=3: print("adding constraints for triple assignment")
		for I in combinations(N,rank):
			constraints0.append([+var_trip(*I,s) for s in ['+','-','?']])
			for s1,s2 in combinations(['+','-','?'],2):
				constraints0.append([-var_trip(*I,s1),-var_trip(*I,s2)])

		if nozeros:
			if DEBUG>=3: print("adding constraints for no-zeros")
			for I in combinations(N,rank):
				constraints0.append([+var_trip(*I,s) for s in ['+','-']])

		if DEBUG>=3: print("adding constraints for packets")
		# signature functions: forbid invalid configuartions 
		for S in forbidden_patterns:
			assert(len(S) == rank+1)
			for I in combinations(N,rank+1):
				Ir = list(combinations(I,rank))
				constraints0.append([-var_trip(*Ir[j],S[j]) for j in range(rank+1)])

		CNF_cached[N,forbidden_patternsstr,nozeros] = constraints0

	constraints = copy(CNF_cached[N,forbidden_patternsstr,nozeros])

	if DEBUG>=3: print("adding constraints for pre-set triples")
	for I in pre_set:
		# pre_set[I] can be a character '+'/'-'/'?' list of options such as ['+','?'] or '+-' 
		constraints.append([var_trip(*I,v) for v in pre_set[I]]) 

	if DEBUG>=3: print("adding constraints for upset-blacklisted confiugrations")
	for Xb in blacklist_upset:
		constraints.append([-var_trip(*I,Xb[I]) for I in Xb if Xb[I]!='?'])

	if DEBUG>=3: print("adding constraints for downset-blacklisted confiugrations")
	for Xb in blacklist_downset:
		constraints.append(
			 [+var_trip(*I,'+') for I in Xb if Xb[I]!='+']
			+[+var_trip(*I,'-') for I in Xb if Xb[I]!='-'])


	if num_zeros_max != None or num_zeros_min != None:
		prev_I = None
		for I in combinations(N,rank):
			constraints.append([+var_numzeros(*I,k) for k in range(maxnumzeros+1)])
			for k1,k2 in combinations(range(maxnumzeros+1),2):
				constraints.append([-var_numzeros(*I,k1),-var_numzeros(*I,k2)])

			if prev_I == None:
				constraints.append([-var_trip(*I,'?'),+var_numzeros(*I,1)])
				constraints.append([+var_trip(*I,'?'),+var_numzeros(*I,0)])
			else:
				for k in range(maxnumzeros+1):
					constraints.append([-var_numzeros(*prev_I,k),+var_trip(*I,'?'),+var_numzeros(*I,k)])
					if k < maxnumzeros:
						constraints.append([-var_numzeros(*prev_I,k),-var_trip(*I,'?'),+var_numzeros(*I,k+1)])
					else:
						constraints.append([-var_numzeros(*prev_I,k),-var_trip(*I,'?')])
			prev_I = I	

		if num_zeros_max != None: constraints.append([+var_numzeros(*prev_I,k) for k in range(num_zeros_max+1)])
		if num_zeros_min != None: constraints.append([+var_numzeros(*prev_I,k) for k in range(num_zeros_min,maxnumzeros+1)])

	if USE_CADICAL: # cadical
		try:
			solver = Cadical153(bootstrap_with=constraints)
		except NameError:
			solver = Cadical(bootstrap_with=constraints) # older versions
		solutions_iterator = solver.enum_models()
	else: # picosat
		solutions_iterator = pycosat.itersolve(constraints)

	found = False

	for sol in solutions_iterator:
		found = True
		sol = set(sol)
		
		X = {}
		for I in combinations(N,rank):
			for s in ['+','-','?']:
				if var_trip(*I,s) in sol: 
					X[I] = s
			assert(I in X)
		yield X

	if not found and verify:
		print("verify unsatisfiability using drat-trim")
		cnf_fp = "_tmp.cnf"
		proof_fp = "_tmp.proof"
		CNF(from_clauses=constraints).to_file(cnf_fp) # write cnf and
		os.system(f"cadical {cnf_fp} {proof_fp} -q > /dev/null") # use cadical to create DRAT unsatisfiability certificate
		assert(os.system(f"drat-trim {cnf_fp} {proof_fp} > /dev/null") == 0) # drat-trim returns 0 when the certificate is valid and 1 on any failure; cf. https://github.com/marijnheule/drat-trim/blob/master/drat-trim.c
