# description: two-layer sat program to find gadgets on 2 variables
# author: manfred scheucher 2023


from basics import *


def test_gadget(X,N,forbidden_patterns4,logic_str,logic_fun,logic_vars,verify=False):
	too_strict = False
	too_loose = False
	for var_assignment in product([True,False],repeat=len(logic_vars)):
	
		for i in range(len(logic_vars)):
			assert(X[logic_vars[i]] == '?')
			X[logic_vars[i]] = '+' if var_assignment[i] == True else '-'

		is_compl = test_completable(X,N,forbidden_patterns4,verify=verify)
		for i in range(len(logic_vars)):
			X[logic_vars[i]] = '?'

		if is_compl < logic_fun(*var_assignment): too_strict = True
		if is_compl > logic_fun(*var_assignment): too_loose  = True

		if too_strict and too_loose: break
	return too_strict,too_loose



def find_gadget_incremental(N,logic_str,logic_fun,logic_vars):
	start_time0 = time.perf_counter()

	vpool = IDPool(start_from=1) 
	all_variables = {}

	# initialize variables
	for a,b,c in combinations(N,3):
		for s in ['+','-','?']:
			all_variables[('trip',(a,b,c,s))] = vpool.id()

	def var(L):	return all_variables[L]
	def var_trip(*L): return var(('trip',L))

	constraints = []
	for v in all_variables.values():
		constraints.append([+v,-v])

	if DEBUG>=3: print("adding constraints for triple assignment")
	for a,b,c in combinations(N,3):
		constraints.append([+var_trip(a,b,c,s) for s in ['+','-','?']])
		for s1,s2 in combinations(['+','-','?'],2):
			constraints.append([-var_trip(a,b,c,s1),-var_trip(a,b,c,s2)])

	if DEBUG>=3: print("adding constraints for packets")
	# signature functions: forbid invalid configuartions 
	for s1,s2,s3,s4 in forbidden_patterns4:
		for a,b,c,d in combinations(N,4):
			constraints.append([-var_trip(a,b,c,s1),-var_trip(a,b,d,s2),-var_trip(a,c,d,s3),-var_trip(b,c,d,s4)])

	# pre-set zeros
	for v in logic_vars:
		constraints.append([+var_trip(*v,'?')])

	if USE_CADICAL:
		try:
			solver = Cadical153(bootstrap_with=constraints)
		except NameError:
			solver = Cadical(bootstrap_with=constraints) # older versions

	ct = 0
	blacklist_upset = 0
	blacklist_downset = 0
	result = None

	#for sol in solver.enum_models():
	while True:
		cur_time = time.perf_counter()
		timed_out_setting = (args.timeout_setting > 0) and (cur_time-start_time > args.timeout_setting)
		timed_out_gadget  = (args.timeout_gadget > 0) and (cur_time-start_time0 > args.timeout_gadget)

		if timed_out_setting | timed_out_gadget:
			global find_gadget_incremental_timed_out
			find_gadget_incremental_timed_out = True 
			if args.DEBUG >= 1: print("\t\t\t\ttimeout!")
			break

		if USE_CADICAL:
			if not solver.solve(): break
			sol = solver.get_model()
		else:
			sol = pycosat.solve(constraints)
			if sol == "UNSAT": break

		ct += 1
		sol = set(sol) # for faster lookup
		X = {(a,b,c):s for a,b,c in combinations(N,3) for s in ['+','-','?'] if var_trip(a,b,c,s) in sol}
		X_str = X_to_str(X,N)
		#print("solution #",ct,":",X_str)#,X)

		if DEBUG>=3: 
			print("blacklisted: up =",blacklist_upset,", down =",blacklist_downset,end="\r")
			stdout.flush()

		too_strict,too_loose = test_gadget(X,N,forbidden_patterns4,logic_str,logic_fun,logic_vars)

		if not too_strict and not too_loose: 
			# found gadget!!
			X_str = X_to_str(X,N)
			result = (len(N),X_str,logic_vars) 
			break

		# search a smallest assignment X_min (by filling up X with zeros) which is too strict
		if too_strict:
			X_min = copy(X)
			while True:
				if args.algorithm == 'basic': break
				num_zeros = list(X_min.values()).count('?')
				assert(num_zeros <= ((n*(n-1)*(n-2))//6))
				if num_zeros == ((n*(n-1)*(n-2))//6): break # all zero excluded => no solutions

				pre_set = {I:{X_min[I],'?'} for I in X_min} # either same or '?'

				found = False
				for X1 in enum_partial(N,forbidden_patterns4,pre_set=pre_set,
						num_zeros_min=num_zeros+1,num_zeros_max=num_zeros+1):
					too_strict1,too_loose1 = test_gadget(X1,N,forbidden_patterns4,logic_str,logic_fun,logic_vars)
					if too_strict1: 
						X_min = copy(X1)
						found = True
						break
				if not found: break
				#if DEBUG: print("-> X_min =",X_to_str(X_min,N))

			#if DEBUG: print("upset-blacklist X_min =",X_to_str(X_min,N))
			blacklist_upset += 1
			if USE_CADICAL:
				solver.add_clause([-var_trip(*I,X_min[I]) for I in X_min if X_min[I]!='?'])
			else:
				constraints.append([-var_trip(*I,X_min[I]) for I in X_min if X_min[I]!='?'])


		# search a largest assignment X_max (by filling up X with non-zeros) which is too loose
		if too_loose:
			X_max = copy(X)
			while True:
				if args.algorithm == 'basic': break
				num_zeros = list(X_max.values()).count('?')
				assert(num_zeros >= 0)

				found = False
				pre_set = {v:'?' for v in logic_vars}|{I:X_max[I] for I in X_max if X_max[I]!='?'}
				for X1 in enum_partial(N,forbidden_patterns4,pre_set=pre_set,
						num_zeros_min=num_zeros-1,num_zeros_max=num_zeros-1):
					too_strict1,too_loose1 = test_gadget(X1,N,forbidden_patterns4,logic_str,logic_fun,logic_vars)
					if too_loose1: 
						X_max = copy(X1)
						found = True
						break
				if not found: break
				#if DEBUG: print("-> X_max =",X_to_str(X_max,N))

			#if DEBUG: print("downset-blacklist X_max =",X_to_str(X_max,N))
			blacklist_downset += 1
			if USE_CADICAL:
				solver.add_clause(
					 [+var_trip(*I,'+') for I in X_max if X_max[I]!='+']
					+[+var_trip(*I,'-') for I in X_max if X_max[I]!='-'])
			else:
				constraints.append(
					 [+var_trip(*I,'+') for I in X_max if X_max[I]!='+']
					+[+var_trip(*I,'-') for I in X_max if X_max[I]!='-'])


	end_time0 = time.perf_counter()
	time_diff0 = end_time0-start_time0

	global test_stats
	test_stats.append({'gadget':logic_str,'found':result!=None,'time':time_diff0,'blacklist_upset':blacklist_upset,'blacklist_downset':blacklist_downset}) # TODO
	# number of clauses: solver.nof_clauses()

	return result


def logic_vars_options(N,num_vars):
	N3 = combinations(N,3)
	for V in combinations(N3,num_vars):
		valid = True
		# assert consecutive
		for I in V:
			if set(I) != set(range(I[0],I[0]+len(I))):
				valid = False
				break

		if valid:
			yield V


gadget2_A_or_B       = 'A or B'
gadget2_A_or_notB    = 'A or not B'
gadget2_notA_or_B    = 'not A or B'
gadget2_notA_or_notB = 'not A or not B'

def find_propagator_gadgets(n,gadgets_found={}):
	gadgets_to_find = [
		gadget2_A_or_B,
		gadget2_A_or_notB,
		gadget2_notA_or_B,
		gadget2_notA_or_notB,
	]

	for logic_str in gadgets_to_find:
		if logic_str in gadgets_found: continue # already known
		if args.DEBUG>=2: print("\t\tsearch propagator gadget",logic_str)
		logic_fun = eval("lambda A,B: "+logic_str)

		N = range(n)
		for logic_vars in logic_vars_options(N,2):
			if args.DEBUG>=2: print("\t\t\tsearch propagator gadget",logic_str,"with logic_vars",logic_vars)
			gadget = find_gadget_incremental(N,logic_str,logic_fun,logic_vars)
			if gadget != None: 
				if args.DEBUG>=2: print (">>> found propagator gadget '"+logic_str+"'"" :",gadget)
				gadgets_found[logic_str] = gadget
				break

	return gadgets_found



gadget3_A_or_B_or_C          = 'A or B or C'
gadget3_A_or_B_or_notC       = 'A or B or not C'
gadget3_A_or_notB_or_C       = 'A or not B or C'
gadget3_A_or_notB_or_notC    = 'A or not B or not C'
gadget3_notA_or_B_or_C       = 'not A or B or C'
gadget3_notA_or_B_or_notC    = 'not A or B or not C'
gadget3_notA_or_notB_or_C    = 'not A or not B or C'
gadget3_notA_or_notB_or_notC = 'not A or not B or not C'

def find_clause_gadgets(n,gadgets_found={},only_search_monotone=False,just_one=False):
	if only_search_monotone:
		gadgets_to_find = [
			gadget3_A_or_B_or_C,
			gadget3_notA_or_notB_or_notC,
		]
	else:
		gadgets_to_find = [
			gadget3_A_or_B_or_C,
			gadget3_A_or_B_or_notC,
			gadget3_A_or_notB_or_C,
			gadget3_A_or_notB_or_notC,
			gadget3_notA_or_B_or_C,
			gadget3_notA_or_B_or_notC,
			gadget3_notA_or_notB_or_C,
			gadget3_notA_or_notB_or_notC,
		]

	for logic_str in gadgets_to_find:
		if logic_str in gadgets_found: continue # already known
		if args.DEBUG>=2: print("\t\tsearch clause gadget",logic_str)
		logic_fun = eval("lambda A,B,C: "+logic_str)

		N = range(n)
		for logic_vars in logic_vars_options(N,3):
			if args.DEBUG>=2: print("\t\t\tsearch clause gadget",logic_str,"with logic_vars",logic_vars)
			gadget = find_gadget_incremental(N,logic_str,logic_fun,logic_vars)
			if gadget != None: 
				if args.DEBUG>=2: print (">>> found propagator gadget '"+logic_str+"'"" :",gadget)
				gadgets_found[logic_str] = gadget
				break

		if gadgets_found and just_one: break

	return gadgets_found




import argparse
parser = argparse.ArgumentParser()
parser.add_argument("fp",type=str,help="file with list of settings")
parser.add_argument("n",type=int,help="number of elements")
parser.add_argument("--timeout_setting","-tos",type=int,default=0,help="set timeout for setting")
parser.add_argument("--timeout_gadget","-tog",type=int,default=0,help="set timeout for gadgets")
parser.add_argument("--algorithm",choices=['advanced','basic'],default='advanced',help="choose basic or advanced algorithm")
parser.add_argument("--certificates_path","-cp",type=str,default=None,help="path for certificates")
parser.add_argument("--DEBUG","-D",type=int,default=0,help="number of elements")
parser.add_argument("--load-certificates","-L",action="store_true",help="load precomputed certificates")
parser.add_argument("--verifyonly","-vo",action="store_true",help="only verify gadgets from existing certificates")
parser.add_argument("--verifydrat","-vd",action="store_true",help="verify models and unsatisfiablity using drat")
#parser.add_argument("--plotstatistics","-ps",action="store_true",help="create plots")
parser.add_argument("--summarize","-s",action="store_false",help="summarize hard settings")


args = parser.parse_args()
vargs = vars(args)
print("c\tactive args:",{x:vargs[x] for x in vargs if vargs[x] != None and vargs[x] != False})

if args.verifyonly:
	args.load_certificates = True
	args.summarize = False
	
if args.certificates_path == None:
	args.certificates_path = f"certificates_{args.algorithm}/"

n = args.n
DEBUG = args.DEBUG

ct0 = 0
ct0_succ = 0
ct0_fail = 0
ct0_to = 0



if args.summarize:
	sumfp = f"{args.fp}.summary_n{n}_{args.algorithm}_{SOLVER}"
	sumfile = open(sumfp,"w")

for line in (open(args.fp).readlines()):
	ct0 += 1
	forbidden_patterns4_orig = literal_eval(line)

	print(80*"#")
	print("# succ",ct0_succ,"/ to",ct0_to,"/ fail",ct0_fail,":",forbidden_patterns4_orig)

	forbidden_patterns4 = forbidden_patterns_filter_free_closure(forbidden_patterns4_orig)
	#print("completed to",forbidden_patterns4)


	NP_hard = False

	if args.load_certificates:
		cert = load_certificate(args.certificates_path,forbidden_patterns4_orig)
		if args.verifyonly: assert(cert)
	else:
		cert = None



	if cert:
		pg = cert['pgadgets']
		cg = cert['cgadgets']
	else:
		pg,cg = {},{}


	find_gadget_incremental_timed_out = False # global variable
	start_time = time.perf_counter()
	test_stats = [] 

	for n0 in range(4,n+1):
		print("**** search on ",n0," elements *****")

		# first search all propagator gadgets
		if not args.verifyonly: 
			pg = find_propagator_gadgets(n0,gadgets_found=pg)
		
		print("\tpropagator gadgets:",len(pg),pg) 
		
		# if all propagator gadgets are found, one clause gadget is sufficient
		if len(pg) == 4 or ((gadget2_A_or_B in pg) and (gadget2_notA_or_notB in pg)):
			if not args.verifyonly and not cg: 
				cg = find_clause_gadgets(n0,gadgets_found=cg,just_one=True)
			if cg:
				NP_hard = True
				print("=> NP-hard because all properators + clause gadgets found")

		# otherwise search specific clause gadgets
		elif len(pg) >= 2:
			if not args.verifyonly and not cg: 
				cg = find_clause_gadgets(n0,gadgets_found=cg,only_search_monotone=True) 
				# only search gadget3_A_or_B_or_C and gadget3_notA_or_notB_or_notC gadget
			
			if (gadget3_A_or_B_or_C in cg) and (gadget2_notA_or_B in pg) and (gadget2_notA_or_notB in pg):
				NP_hard = True
				print("=> NP-hard because positive monotone clause + right propagations")

			elif (gadget3_A_or_B_or_C in cg) and (gadget2_A_or_notB in pg) and (gadget2_notA_or_notB in pg):
				NP_hard = True
				print("=> NP-hard because positive monotone clause + left propagations")

			elif (gadget3_notA_or_notB_or_notC in cg) and (gadget2_A_or_B in pg) and (gadget2_A_or_notB in pg):
				NP_hard = True
				print("=> NP-hard because negative monotone clause + right propagations")

			elif (gadget3_notA_or_notB_or_notC in cg) and (gadget2_A_or_B in pg) and (gadget2_notA_or_B in pg):
				NP_hard = True
				print("=> NP-hard because negative monotone clause + left propagations")

		print("\tclause gadgets:",len(cg),cg) 

		if NP_hard: break

		cur_time = time.perf_counter()
		time_diff = cur_time-start_time
		if (args.timeout_setting > 0) and (time_diff > args.timeout_setting): break


	end_time = time.perf_counter()
	time_diff = end_time-start_time
	timed_out = (args.timeout_setting > 0 and time_diff > args.timeout_setting) or find_gadget_incremental_timed_out

	if find_gadget_incremental_timed_out:
		timed_out = True

	if DEBUG:
		print(f"computing time: {time_diff} seconds")

	if cert: assert(NP_hard) 

	if timed_out:
		ct0_to += 1
		print("=> timeout")

	elif NP_hard:
		ct0_succ += 1

		if not cert: 
			cert = {'fpatterns':forbidden_patterns4_orig,'pgadgets':pg,'cgadgets':cg,'n':n}
			create_certificate(args.certificates_path,cert)

		
		#verify gadgets
		gadgets = pg|cg
		for logic_str in gadgets:
			m,X_str,logic_vars = gadgets[logic_str]
			X = X_from_str(X_str,range(m))
			if logic_str in pg: logic_fun = eval("lambda A,B: "+logic_str)
			if logic_str in cg: logic_fun = eval("lambda A,B,C: "+logic_str)
			too_strict,too_loose = test_gadget(X,range(m),forbidden_patterns4_orig,logic_str,logic_fun,logic_vars,verify=args.verifydrat)
			assert(too_strict == False and too_loose == False)
		print("#all gadgets verified")

	else:
		ct0_fail += 1
		print("=> unknown")


	if args.summarize:
		if NP_hard: 
			status = 'succ'
		elif timed_out or find_gadget_incremental_timed_out: 
			status = 'timeout'
		else:
			status = 'fail'

		summary = {
			'fpatterns' :forbidden_patterns4_orig,
			'status'    :status,
			'total_time':time_diff,
			'tests'     :test_stats,
			}
		sumfile.write(str(summary)+"\n")

		print("total time:",time_diff,sum(s['time'] for s in test_stats))
	print()

print("hard   :",ct0_succ,"/",ct0)
print("fail   :",ct0_fail,"/",ct0)
print("timeout:",ct0_to  ,"/",ct0)

if args.summarize:
	print(f"wrote summary to {sumfp}")

