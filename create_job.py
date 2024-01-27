from sys import *

path = argv[1]
n = int(argv[2])

params = path+" "+str(n)
params_ = path+"_"+str(n)
params_short = params_.split("/")[-1]  if "/" in params_  else params_

with open(params_+".job","w") as f: 
    f.write("#!/bin/bash --login\n")
    f.write(f"#SBATCH --job-name={params_short}\n")
    f.write(f"#SBATCH --output={params_short}.out\n")
    #f.write("#SBATCH --mem=30G\n")
    f.write("#SBATCH --time=168:00:00\n")
    #f.write("#SBATCH --cpus-per-task=32\n")
    f.write("#SBATCH --mail-user=scheucher@math.tu-berlin.de\n")
    f.write("#SBATCH --mail-type=BEGIN,END\n")
    f.write("time python3 find_gadgets_new.py "+params+" --algorithm advanced\n")
    f.write("time python3 find_gadgets_new.py "+params+" --algorithm basic\n")
