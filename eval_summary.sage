from ast import literal_eval
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("fp",type=str,help="file with summary")

args = parser.parse_args()
vargs = vars(args)
print("c\tactive args:",{x:vargs[x] for x in vargs if vargs[x] != None and vargs[x] != False})


summary = []
for line in open(args.fp):
	entry = literal_eval(line)
	print("entry",entry)
	assert(type(entry) == dict)
	summary.append(entry)




def plot_stat(stat,group,color):
	plt = []
	for i in range(1,len(stat)):
		plt.append(line2d([(i,stat[i-1]),(i+1,stat[i])],color='black',zorder=-9))

	for i in range(len(stat)):
		color1 = color if group[i] else 'white'
		marker = ',' if group[i] else 'o'
		markeredgecolor = None if group[i] else color
		plt.append(point2d((i+1,stat[i]),color=color1,markeredgecolor=markeredgecolor,marker=marker,size=40))
	return plt


if 1:
	stat = [(entry['total_time'],entry['certified_hard']) for entry in summary]
	time,hard = zip(*sorted(stat))

	plt = []
	plt += plot_stat(time,hard,'red')

	plt_file = args.fp + ".time.pdf"
	sum(plt).save(plt_file)	
	print("plotted time statistic to file:",plt_file)



if 1:
	stat = []
	for entry in summary:
		tests = entry['test_stats']
		hard = entry['certified_hard']
		u = 0
		d = 0
		for test in tests:
			u += test['blacklist_upset']
			d += test['blacklist_downset']
		stat.append((u+d,u,d,hard))

	total,up,down,hard = zip(*sorted(stat))

	plt = []
	plt += plot_stat(total,hard,'black')
	plt += plot_stat(up,hard,'red')
	plt += plot_stat(down,hard,'blue')

	plt_file = args.fp + ".blacklist.pdf"
	sum(plt).save(plt_file)	
	print("plotted time statistic to file:",plt_file)


