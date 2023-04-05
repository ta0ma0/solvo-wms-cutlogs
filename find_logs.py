from subprocess import PIPE, Popen


def search_planner_log(planner_error_time):
	"""
	Search planner log file, where timestamp from wmsmc_server.log
	
	:planner_error_time: time error converted from wmsmc error time format
	with function planner_time()

	:returns: planner log file path where finding timestamp equal wmsmc error time.
	"""
	path_to_plnr_logs = '~/tmp/'
	planner_log_file_name = 'planner.log'
	args_find = ['find', path_to_plnr_logs, '--type', 'f', '--name',
	planner_log_file_name]
	args_find.extend(glob.glob('%s*' % planner_log_file)) 
	plnr_search = subprocess.Popen(args_find, stdout=PIPE)
	plnr_filenames = plnr_search.communicate()[0].split()
	return plnr_filenames
