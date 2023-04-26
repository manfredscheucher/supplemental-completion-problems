# description: two-layer sat program to find gadgets on 2 variables
# author: manfred scheucher 2023

from basics import *



def test_gadget(X,N,forbidden_patterns4,logic_str,logic_fun,logic_vars):
	too_strict = False
	too_loose = False
	for var_assignment in product([True,False],repeat=len(logic_vars)):
	
		for i in range(len(logic_vars)):
			assert(X[logic_vars[i]] == '0')
			X[logic_vars[i]] = '+' if var_assignment[i] == True else '-'

		is_compl = test_completable(X,N,forbidden_patterns4)
		for i in range(len(logic_vars)):
			X[logic_vars[i]] = '0'

		if is_compl < logic_fun(*var_assignment): too_strict = True
		if is_compl > logic_fun(*var_assignment): too_loose  = True

		if too_strict and too_loose: break
	return too_strict,too_loose



def find_gadget(N,logic_str,logic_fun,logic_vars):
	blacklist_upset = []
	blacklist_downset = []

	ct = 0
	try:
		while True:
			ct += 1
			X = next(enum_partial(N,forbidden_patterns4,pre_set={v:'0' for v in logic_vars},
					blacklist_upset=blacklist_upset,blacklist_downset=blacklist_downset))
		
			if DEBUG: 
				print("testsig",ct,X_to_str(X,N),":",len(blacklist_upset),"+",len(blacklist_downset),end="\r")
				stdout.flush()

			too_strict,too_loose = test_gadget(X,N,forbidden_patterns4,logic_str,logic_fun,logic_vars)

			if not too_strict and not too_loose: 
				# found gadget!!
				X_str = X_to_str(X,N)
				return (len(N),X_str,logic_vars) 


			# search a smallest assignment X_min (by filling up X with zeros) which is too strict
			if too_strict:
				#if DEBUG: print("too_strict X =",X_to_str(X,N))
				X_min = copy(X)
				while True:
					num_zeros = list(X_min.values()).count('0')
					assert(num_zeros <= ((n*(n-1)*(n-2))//6))
					if num_zeros == ((n*(n-1)*(n-2))//6): break # all zero excluded => no solutions

					pre_set = {I:{X_min[I],'0'} for I in X_min} # either same or '0'

					found = False
					for X1 in enum_partial(N,forbidden_patterns4,pre_set=pre_set,
							blacklist_upset=blacklist_upset,blacklist_downset=blacklist_downset,
							num_zeros_min=num_zeros+1,num_zeros_max=num_zeros+1):
						too_strict1,too_loose1 = test_gadget(X1,N,forbidden_patterns4,logic_str,logic_fun,logic_vars)
						if too_strict1: 
							X_min = copy(X1)
							found = True
							break
					if not found: break
					#if DEBUG: print("-> X_min =",X_to_str(X_min,N))

				#if DEBUG: print("upset-blacklist X_min =",X_to_str(X_min,N))
				blacklist_upset.append(X_min)


			# search a largest assignment X_max (by filling up X with non-zeros) which is too loose
			if too_loose:
				#if DEBUG: print("too_loose X =",X_to_str(X,N))
				X_max = copy(X)
				while True:
					num_zeros = list(X_max.values()).count('0')
					assert(num_zeros >= 0)

					found = False
					pre_set = {v:'0' for v in logic_vars}|{I:X_max[I] for I in X_max if X_max[I]!='0'}
					for X1 in enum_partial(N,forbidden_patterns4,pre_set=pre_set,
							blacklist_upset=blacklist_upset,blacklist_downset=blacklist_downset,
							num_zeros_min=num_zeros-1,num_zeros_max=num_zeros-1):
						too_strict1,too_loose1 = test_gadget(X1,N,forbidden_patterns4,logic_str,logic_fun,logic_vars)
						if too_loose1: 
							X_max = copy(X1)
							found = True
							break
					if not found: break
					#if DEBUG: print("-> X_max =",X_to_str(X_max,N))

				#if DEBUG: print("downset-blacklist X_max =",X_to_str(X_max,N))
				blacklist_downset.append(X_max)

	except StopIteration:				
		#print ("stop. did not find gadget.")
		return None



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



def find_propagator_gadgets(nmax):

	gadgets_to_find = [
		'A or B',
		'A or not B',
		'not A or B',
		'not A or not B'
	]

	gadgets_found = {}
	for logic_str in list(gadgets_to_find):
		print("\tsearch propagator gadget",logic_str)
		logic_fun = eval("lambda A,B: "+logic_str)

		for n in range(4,nmax+1):
			N = range(n)
			print("\t\tsearch on ",n," elements")
			for logic_vars in logic_vars_options(N,2):
				print("\t\t\tsearch propagator gadget",logic_str,"with logic_vars",logic_vars)
				gadget = find_gadget(N,logic_str,logic_fun,logic_vars)
				if gadget != None: 
					print (">>> found propagator gadget '"+logic_str+"'"" :",gadget)
					gadgets_found[logic_str] = gadget
					break
			if logic_str in gadgets_found: break

	return gadgets_found




def find_clause_gadgets(nmax,only_search_monotone=False,just_one=False):
	if only_search_monotone:
		gadgets_to_find = [
			'A or B or C'            ,
			'not A or not B or not C',
		]
	else:
		gadgets_to_find = [
			'A or B or C'            ,
			'A or B or not C'        ,
			'A or not B or C'        ,
			'A or not B or not C'    ,
			'not A or B or C'        ,
			'not A or B or not C'    ,
			'not A or not B or C'    ,
			'not A or not B or not C',
		]

	gadgets_found = {}
	for logic_str in list(gadgets_to_find):
		print("\tsearch clause gadget",logic_str)
		logic_fun = eval("lambda A,B,C: "+logic_str)

		for n in range(4,nmax+1):
			N = range(n)
			print("\t\tsearch on ",n," elements")
			for logic_vars in logic_vars_options(N,3):
				print("\t\t\tsearch clause gadget",logic_str,"with logic_vars",logic_vars)
				gadget = find_gadget(N,logic_str,logic_fun,logic_vars)
				if gadget != None: 
					print (">>> found propagator gadget '"+logic_str+"'"" :",gadget)
					gadgets_found[logic_str] = gadget
					break
			if logic_str in gadgets_found: break

		if gadgets_found and just_one: break

	return gadgets_found




import argparse
parser = argparse.ArgumentParser()
parser.add_argument("fp",type=str,help="file with list of settings")
parser.add_argument("n",type=int,help="number of elements")
parser.add_argument("--certificates_path","-cp",type=str,default="certificates5/",help="path for certificates")
parser.add_argument("--DEBUG","-D",action="store_true",help="number of elements")
parser.add_argument("--verify","-v",action="store_false",help="verify all gadgets")
parser.add_argument("--verifyonly","-vo",action="store_true",help="only verify gadgets from existing certificates")
parser.add_argument("--summarize","-le",type=str,help="summarize hard settings")

args = parser.parse_args()
vargs = vars(args)
print("c\tactive args:",{x:vargs[x] for x in vargs if vargs[x] != None and vargs[x] != False})


n = args.n
#N = range(n)
DEBUG = args.DEBUG

ct0 = 0
ct0_hard = 0

#hard_file = open(args.fp+".2hard"+str(n)+".txt","w")
#unknown_file = open(args.fp+".2unknown"+str(n)+".txt","w")
#cg_file = open(args.fp+".cg"+str(n)+"_"+str(args.zmin)+".txt","w")

if args.summarize:
	sumfile = open(args.summarize,"w")

for line in (open(args.fp).readlines()):
	ct0 += 1
	forbidden_patterns4_orig = literal_eval(line)

	print(80*"#")
	print("#",ct0_hard,"/",ct0,":",forbidden_patterns4_orig)

	forbidden_patterns4 = forbidden_patterns_filter_free_closure(forbidden_patterns4_orig)
	#print("completed to",forbidden_patterns4)


	NP_hard = False

	cert = load_certificate(args.certificates_path,forbidden_patterns4_orig)
	if cert:
		pg,cg = cert
	else:
		pg,cg = [],[]


	# first search all propagator gadgets
	if not args.verifyonly and not pg: 
		pg = find_propagator_gadgets(n)
	
	print("pg:",len(pg),pg) 
	
	# based on how which propagators found, search clause gadgets
	if len(pg) == 4:
		if not args.verifyonly and not cg: 
			cg = find_clause_gadgets(n,just_one=True)
		if cg:
			NP_hard = True
			print("=> NP-hard because all properators + clause gadgets found")

	elif len(pg) >= 2:
		if not args.verifyonly and not cg: 
			cg = find_clause_gadgets(n,only_search_monotone=True) 
			# only search "A or B or C" and "not A or not B or not C" gadget
		
		if ("A or B or C" in cg) and ("not A or B" in pg) and ("not A or not B" in pg):
			NP_hard = True
			print("=> NP-hard because positive monotone clause + right propagations")

		elif ("A or B or C" in cg) and ("A or not B" in pg) and ("not A or not B" in pg):
			NP_hard = True
			print("=> NP-hard because positive monotone clause + left propagations")

		elif ("not A or not B or not C" in cg) and ("A or B" in pg) and ("A or not B" in pg):
			NP_hard = True
			print("=> NP-hard because negative monotone clause + right propagations")

		elif ("not A or not B or not C" in cg) and ("A or B" in pg) and ("not A or B" in pg):
			NP_hard = True
			print("=> NP-hard because negative monotone clause + left propagations")

	print("cg:",len(cg),cg) 

	
	if cert: assert(NP_hard)


	if NP_hard:
		ct0_hard += 1

		if not cert: 
			create_certificate(args.certificates_path,forbidden_patterns4_orig,pg,cg)

		if args.verify:
			gadgets = pg|cg
			for logic_str in gadgets:
				m,X_str,logic_vars = gadgets[logic_str]
				X = X_from_str(X_str,range(m))
				if logic_str in pg: logic_fun = eval("lambda A,B: "+logic_str)
				if logic_str in cg: logic_fun = eval("lambda A,B,C: "+logic_str)
				too_strict,too_loose = test_gadget(X,range(m),forbidden_patterns4_orig,logic_str,logic_fun,logic_vars)
				assert(too_strict == False and too_loose == False)
			print("#all gadgets verified")

		if args.summarize:
			#line_latex = line.replace(" ","").replace("[","\\{").replace("]","\\}").replace("'",'')
			#line_latex = line_latex.replace("\n",",\n")
			#sumfile.write(line_latex)
			sumfile.write(line)

	else:
		print("=> unknown")

	print()

print("hard:",ct0_hard,"/",ct0)
