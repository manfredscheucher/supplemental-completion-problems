from sys import *

path = argv[1]
n = int(argv[2])

params = path+" "+str(n)
params_ = path+"_"+str(n)
path_short = path.split("/")[-1]  if "/" in params_  else params_

for algo in ['basic','advanced']:
    name = path_short+algo[0]+str(n)
    fp = params_+algo[0]+".job"
    print("create job file",fp)
    with open(fp,"w") as f: 
        f.write("#!/bin/bash --login\n")
        f.write(f"#SBATCH --job-name={name}\n")
        f.write(f"#SBATCH --output={fp}.out\n")
        #f.write("#SBATCH --mem=30G\n")
        f.write("#SBATCH --time=12:00:00\n")
        #f.write("#SBATCH --cpus-per-task=32\n")
        #f.write("#SBATCH --mail-user=scheucher@math.tu-berlin.de\n")
        #f.write("#SBATCH --mail-type=BEGIN,END\n")
        f.write("time python3 find_gadgets_new.py "+params+" --timeoutgadget 300 --algorithm "+algo+"\n")
