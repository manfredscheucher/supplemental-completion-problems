from itertools import *
from more_itertools import powerset


import argparse
parser = argparse.ArgumentParser()
parser.add_argument("rank",type=int,help="rank")
args = parser.parse_args()

rank = args.rank

potential = [P for P in [''.join(P) for P in product('+-',repeat=rank+1)] if P.count('-+')+P.count('+-') == rank]
print(potential)