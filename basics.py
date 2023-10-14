from itertools import *
from ast import *
from sys import *
from copy import *
from pysat.formula import IDPool,CNF
from pysat.solvers import *

import os.path



def X_to_str(X,N):
	return ''.join(X[a,b,c] for a,b,c in combinations(N,3))


def X_from_str(s,N):
	assert(len(list(combinations(N,3))) == len(s))
	return {(a,b,c): s[i] for i,(a,b,c) in enumerate(combinations(N,3))}





def load_certificate(certificates_path,forbidden_patterns4):
	forbidden_patterns4str = ','.join(sorted(forbidden_patterns4))
	fp = certificates_path+forbidden_patterns4str+".txt"
	if not os.path.exists(fp):
		return None
	print("## load certificate from "+fp)
	s,pg,cg = literal_eval(open(fp).readline())
	assert(s == forbidden_patterns4)
	return pg,cg


def create_certificate(certificates_path,forbidden_patterns4,pg,cg):
	if not os.path.exists(certificates_path): os.makedirs(certificates_path)
	forbidden_patterns4str = ','.join(sorted(forbidden_patterns4))
	fp = certificates_path+forbidden_patterns4str+".txt"
	assert(not os.path.exists(fp)) # do not overwrite existing certificates
	with open(fp,"w") as f:
		f.write(str(tuple([forbidden_patterns4,pg,cg]))+"\n")
	print("## wrote certificate to "+fp)



CNF_cached = {}

def forbidden_patterns_closure(forbidden_patterns4):
	solution_patterns4 = [list(pattern) for pattern in product(['+','-'],repeat=4) if ''.join(pattern) not in forbidden_patterns4]

	closure = set(forbidden_patterns4)
	for pattern in product(['+','-','0'],repeat=4):
		pattern = ''.join(pattern)
		completable = False
		for sol in solution_patterns4:
			if not [i for i in range(4) if pattern[i] != '0' and pattern[i] != sol[i]]:
				completable = True
		if not completable:
			closure.add(pattern)
	return closure


def forbidden_patterns_filter_free_closure(forbidden_patterns4):
	solution_patterns4 = [list(pattern) for pattern in product(['+','-'],repeat=4) if ''.join(pattern) not in forbidden_patterns4]

	closure = set(forbidden_patterns4)
	for pattern in product(['+','-','0'],repeat=4):
		pattern = ''.join(pattern)
		completable = False
		for sol in solution_patterns4:
			if not [i for i in range(4) if pattern[i] != '0' and pattern[i] != sol[i]]:
				completable = True

		# every zero must be completable to both, plus and minus
		all_zeros_free = True
		for k in range(4):
			if pattern[k] == '0':
				for s in ['+','-']:
					pattern_fill = pattern[:k]+s+pattern[k+1:]
					completable_fill = False
					for sol in solution_patterns4:
						if not [i for i in range(4) if pattern_fill[i] != '0' and pattern_fill[i] != sol[i]]:
							completable_fill = True
					if not completable_fill:
						all_zeros_free = False

		if not completable or not all_zeros_free:
			closure.add(pattern)

	return closure

	
def test_completable(X,N,forbidden_patterns4,verify=False):
	X_nonzero = {I:X[I] for I in X if X[I] != '0'}
	for sol in enum_partial(N,forbidden_patterns4,nozeros=True,pre_set=X_nonzero,verify=verify):
		return True
	return False



def enum_partial(N,forbidden_patterns4,nozeros=False,DEBUG=False,pre_set={},
		num_zeros_max=None,num_zeros_min=None,blacklist_upset=[],blacklist_downset=[],verify=False):

	all_variables = [('trip',(a,b,c,s)) for a,b,c in combinations(N,3) for s in ['+','-','0']]

	if num_zeros_max != None or num_zeros_min != None:
		maxnumzeros = len(list(combinations(N,3)))
		all_variables += [('numzeros',(a,b,c,k)) for a,b,c in combinations(N,3) for k in range(maxnumzeros+1)]


	all_variables_index = {}

	_num_vars = 0
	for v in all_variables:
		all_variables_index[v] = _num_vars
		_num_vars += 1

	def var(L):	return 1+all_variables_index[L]
	def var_trip(*L): return var(('trip',L))
	def var_numzeros(*L): return var(('numzeros',L))


	global CNF_cached	

	forbidden_patterns4str = ','.join(sorted(forbidden_patterns4))
	if (N,forbidden_patterns4str,nozeros) not in CNF_cached:

		constraints0 = []

		if DEBUG: print("adding constraints for triple assignment")
		for a,b,c in combinations(N,3):
			constraints0.append([+var_trip(a,b,c,s) for s in ['+','-','0']])
			for s1,s2 in combinations(['+','-','0'],2):
				constraints0.append([-var_trip(a,b,c,s1),-var_trip(a,b,c,s2)])

		if nozeros:
			if DEBUG: print("adding constraints for no-zeros")
			for a,b,c in combinations(N,3):
				constraints0.append([+var_trip(a,b,c,s) for s in ['+','-']])

		if DEBUG: print("adding constraints for packets")
		# signature functions: forbid invalid configuartions 
		for s1,s2,s3,s4 in forbidden_patterns4:
			for a,b,c,d in combinations(N,4):
				constraints0.append([-var_trip(a,b,c,s1),-var_trip(a,b,d,s2),-var_trip(a,c,d,s3),-var_trip(b,c,d,s4)])

		CNF_cached[N,forbidden_patterns4str,nozeros] = constraints0

	constraints = copy(CNF_cached[N,forbidden_patterns4str,nozeros])

	if DEBUG: print("adding constraints for pre-set triples")
	for I in pre_set:
		# pre_set[I] can be a character '+'/'-'/'0' list of options such as ['+','0'] or '+-' 
		constraints.append([var_trip(*I,v) for v in pre_set[I]]) 

	if DEBUG: print("adding constraints for upset-blacklisted confiugrations")
	for Xb in blacklist_upset:
		constraints.append([-var_trip(*I,Xb[I]) for I in Xb if Xb[I]!='0'])

	if DEBUG: print("adding constraints for downset-blacklisted confiugrations")
	for Xb in blacklist_downset:
		constraints.append(
			 [+var_trip(*I,'+') for I in Xb if Xb[I]!='+']
			+[+var_trip(*I,'-') for I in Xb if Xb[I]!='-'])


	if num_zeros_max != None or num_zeros_min != None:
		prev_I = None
		for I in combinations(N,3):
			constraints.append([+var_numzeros(*I,k) for k in range(maxnumzeros+1)])
			for k1,k2 in combinations(range(maxnumzeros+1),2):
				constraints.append([-var_numzeros(*I,k1),-var_numzeros(*I,k2)])

			if prev_I == None:
				constraints.append([-var_trip(*I,'0'),+var_numzeros(*I,1)])
				constraints.append([+var_trip(*I,'0'),+var_numzeros(*I,0)])
			else:
				for k in range(maxnumzeros+1):
					constraints.append([-var_numzeros(*prev_I,k),+var_trip(*I,'0'),+var_numzeros(*I,k)])
					if k < maxnumzeros:
						constraints.append([-var_numzeros(*prev_I,k),-var_trip(*I,'0'),+var_numzeros(*I,k+1)])
					else:
						constraints.append([-var_numzeros(*prev_I,k),-var_trip(*I,'0')])
			prev_I = I	

		if num_zeros_max != None: constraints.append([+var_numzeros(*prev_I,k) for k in range(num_zeros_max+1)])
		if num_zeros_min != None: constraints.append([+var_numzeros(*prev_I,k) for k in range(num_zeros_min,maxnumzeros+1)])

	try:
		solver = Cadical153(bootstrap_with=constraints)
	except ImportError:
		solver = Cadical(bootstrap_with=constraints) # older versions

	found = False

	for sol in solver.enum_models():
		found = True
		sol = set(sol)
		if verify:
			for c in constraints:
				assert(set(c)&sol) # verify solution is valid
		
		solver.add_clause([-x for x in sol]) # exclude this solution
		X = {}
		for a,b,c in combinations(N,3):
			for s in ['+','-','0']:
				if var_trip(a,b,c,s) in sol: 
					X[a,b,c] = s
			assert((a,b,c) in X)
		yield X

	if not found and verify:
		print("verify unsatisfiability using drat-trim")
		cnf_fp = "_tmp.cnf"
		proof_fp = "_tmp.proof"
		CNF(from_clauses=constraints).to_file(cnf_fp) # write cnf and
		os.system(f"cadical {cnf_fp} {proof_fp} -q > /dev/null") # use cadical to create DRAT unsatisfiability certificate
		assert(os.system(f"drat-trim {cnf_fp} {proof_fp} > /dev/null") == 0) # drat-trim returns 0 when the certificate is valid and 1 on any failure; cf. https://github.com/marijnheule/drat-trim/blob/master/drat-trim.c
