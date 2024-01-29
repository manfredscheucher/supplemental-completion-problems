from sys import *

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("fp",type=str,help="file with list of settings")
parser.add_argument("rank",type=int,help="rank")
parser.add_argument("n",type=int,help="number of elements")
parser.add_argument("--timeout_setting","-tos",type=int,default=0,help="set timeout for setting")
parser.add_argument("--timeout_gadget","-tog",type=int,default=0,help="set timeout for gadgets")
#parser.add_argument("--algorithm",choices=['advanced','basic'],default='advanced',help="choose basic or advanced algorithm")
args = parser.parse_args()

path = args.fp
n = args.n

params = path+" "+str(n)
params_ = path+"_"+str(n)
path_short = path.split("/")[-1]  if "/" in params_  else params_

for algo in ['basic','advanced']:
    name = path_short+algo[0]+str(n)
    job_file = params_+algo[0]+".job"
    print("create job file",job_file)
    with open(job_file,"w") as f: 
        f.write("#!/bin/bash --login\n")
        f.write(f"#SBATCH --job-name={name}\n")
        f.write(f"#SBATCH --output={job_file}.out\n")
        #f.write("#SBATCH --mem=30G\n")
        f.write("#SBATCH --time=168:00:00\n")
        #f.write("#SBATCH --cpus-per-task=32\n")
        #f.write("#SBATCH --mail-user=scheucher@math.tu-berlin.de\n")
        #f.write("#SBATCH --mail-type=BEGIN,END\n")
        f.write(f"time python3 find_gadgets_new.py {path} {rank} {n} -tos {args.timeout_setting} -tog {args.timeout_gadget} --algorithm {algo}\n")
