from ast import literal_eval
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("fp",type=str,help="file with summary")
parser.add_argument("--point-size","-s",type=int,default=10,help="size of points")

args = parser.parse_args()
vargs = vars(args)
print("c\tactive args:",{x:vargs[x] for x in vargs if vargs[x] != None and vargs[x] != False})


summary = []
for line in open(args.fp):
	entry = literal_eval(line)
	assert(type(entry) == dict)
	assert('total_time' in entry) 
	assert('status' in entry) 
	assert('tests' in entry) 
	summary.append(entry)




def plot_stat(prop,status,color):
	plt = []
	for i in range(1,len(prop)):
		plt.append(line2d([(i,prop[i-1]),(i+1,prop[i])],color=color,zorder=-9))

	for i in range(len(prop)):
		if status[i] == 'fail':
			color1 = color
			marker = ','
			markeredgecolor = None
		elif status[i] == 'timeout':
			color1 = color
			marker = 'x'
			markeredgecolor = None
		elif status[i] == 'succ':
			color1 = 'white'
			marker = 'o'
			markeredgecolor = color


		plt.append(point2d((i+1,prop[i]),color=color1,markeredgecolor=markeredgecolor,marker=marker,size=args.point_size))
	return plt


print(f"certified settings: {len([e for e in summary if e['status'] == 'succ'])} of {len(summary)} settings")
print(f"failed settings: {len([e for e in summary if e['status'] == 'fail'])} of {len(summary)} settings")
print(f"timeout settings: {len([e for e in summary if e['status'] == 'timeout'])} of {len(summary)} settings")

print(f"total computing time: {sum(entry['total_time'] for entry in summary)}")

if 1:
	stat = [(entry['total_time'],entry['status']) for entry in summary]
	time,status = zip(*sorted(stat))

	print("time",time)

	plt = []
	plt += plot_stat(time,status,'red')

	plt_file = args.fp + ".time.pdf"
	sum(plt).save(plt_file)	
	print("plotted time statistic to file:",plt_file)



if 1:
	stat = []
	for entry in summary:
		tests = entry['tests']
		status = entry['status']
		u = 0
		d = 0
		for test in tests:
			u += test['blacklist_upset']
			d += test['blacklist_downset']
		stat.append((u+d,u,d,status))

	total,up,down,status = zip(*sorted(stat))

	plt = []
	plt += plot_stat(total,status,'black')
	plt += plot_stat(up   ,status,'red'  )
	plt += plot_stat(down ,status,'blue' )

	plt_file = args.fp + ".blacklist.pdf"
	sum(plt).save(plt_file)	
	print("plotted time statistic to file:",plt_file)


