import optparse
from datetime import datetime, timedelta
import subprocess
from subprocess import PIPE, Popen
import glob
from datetime import datetime
from datetime import timedelta
import time
import os
import sys
import constants


work_dir_path = os.getcwd()
work_dir_path_list = work_dir_path.split("/")
logs_dir = work_dir_path_list[-2]
if logs_dir != "tmp":
	print "\033[91m" + "ERROR: Wrong directory, run script in '$SPOOL/cutlogs-0.0.*/' dir" + "\033[0m"
	sys.exit()



hostname = subprocess.Popen(['hostname'], stdout=PIPE)
postfix_logname = hostname.communicate()[0].split()[0] + '.bug'

er_time = ''
parser = optparse.OptionParser()
parser.add_option('--er_time', '-t', action='store', dest='time', help='Error time')
parser.add_option('--log_name', '-n', action='store', dest='log_name', help='Log name')

def sed_b_time_fwmsmc(before_time):
	"""
	Convert datatime before error timestamp to
	wmsmc_server.log format for sed regex.

	:before_time datatime format param calculated from error timestamp and
	several minutes early error.

	:returns: 'sed' format timestamp before error
	"""
	sed_b_time = str(before_time).split()
	sed_b_time = sed_b_time[0] + 'T' + sed_b_time[1]
	return sed_b_time

def sed_a_time_fwmsmc(after_time):
	"""
	Convert datatime after error timestamp to
	wmsmc_server.log format for sed regex.

	:after_time: datatime format param calculated from error timestamp and
	several minutes later error.

	:returns: 'sed' format timestamp after error
	"""
	sed_a_time = str(after_time).split()
	sed_a_time = sed_a_time[0] + 'T' + sed_a_time[1]
	return sed_a_time

def sed_b_time_plnr(before_time):
	"""
	Convert datatime before error timestamp to
	planner.log format for sed regex.

	:before_time: datatime format param calculated from error timestamp and
	several minutes early error.

	:returns: 'sed' format timestamp before error
	"""
	sed_b_time = str(before_time).split()
	sed_b_time_date = sed_b_time[0].split('-')
	sed_b_time_hours = sed_b_time[1]
	sed_b_time_date_plnr = sed_b_time_date[2] + '-' + sed_b_time_date[1] + '-' + sed_b_time_date[0]
	sed_b_time = sed_b_time_date_plnr + ' ' + sed_b_time_hours
	return sed_b_time

def sed_a_time_plnr(after_time):
	"""
	Convert datatime after error timestamp to
	lanner.log format for sed regex.

	:after_time: datatime format param calculated from error timestamp and
	several minutes later error.

	:returns: 'sed' format timestamp after error
	"""
	sed_a_time = str(after_time).split()
	sed_a_time_date = sed_a_time[0].split('-')
	sed_a_time_hours = sed_a_time[1]
	sed_a_time_date_plnr = sed_a_time_date[2] + '-' + sed_a_time_date[1] + '-' + sed_a_time_date[0]
	sed_a_time = sed_a_time_date_plnr + ' ' + sed_a_time_hours
	return sed_a_time

def sed_file(args_sed, out_file):
	"""
	Call linux 'sed' with args.
	
	:args_sed: 'sed' arguments add before call this function.
	"""
	subprocess.call(args_sed, stdout=out_file)

def sed_and_write(sed_b_time, sed_a_time, file_log_path):
	"""
	Call linux 'sed' with before error timestamp and after error timestamp.

	:sed_b_time: wmsmc log format timestamp before error
	:sed_a_time: wmsmc log format timestamp before error

	:returns: name output file
	
	"""
	sed_word = '/%s/,/%s/p' % (sed_b_time, sed_a_time)
	file_name = file_log_path.split("/")[1]
#	print "Debug!!! " +  file_log_path
	if file_name == 'watch':
		file_name = 'solvo-sm.log'
	outp = os.getcwd() + "/" + file_name + '_' + postfix_logname
	print os.getcwd()
	out_file = open(outp, "w")
	args_sed = ['sed', '-n', sed_word, file_log_path]
	print args_sed
	sed_file(args_sed, out_file)
	out_file.close()
	print "Data writed in file: %s" % (outp)
	archivation(outp)
#	subprocess.call(["rm", outp])
#	print "File %s deleted" % (outp)
	return outp

def archivation(file_name):
	args_tar = ['gzip', file_name]
	subprocess.call(args_tar)
	print "Archive created: %s" % (file_name + '.gz') 

def check_file(outp):
	"""
	Check output file before call 'sed', if file is empty
	show warning

	:outp: name output file after call 'sed'

	:returns: True if file is not empty, False if file is empty.
	"""
	result_log = open(outp, 'r')
	check_string = result_log.readlines()
	result_log.close()
	if len(check_string) == 0:
		print '\033[93m' + \
	"""
	WARNING!: Utilite sed don't find strings %s, %s
	in file %s, trying find again with +1 seconds
	""" %(sed_b_time, sed_a_time, file_name[0])
		print '\033[0m'
		return False
	return True

def grep_time(g_args):
	"""
	Find before error time stamp in wmsmc_server.log.

	:g_args: arguments for linux 'grep'.
	
	:returns: grep search result noting or finding strings.
	"""
	grep_time = subprocess.Popen(g_args, stdout=PIPE)
	result = grep_time.communicate()[0].split()
	return result

def search_planner_log(planner_error_time):
	"""
	Search planner log file, where timestamp from wmsmc_server.log
	
	:planner_error_time: time error converted from wmsmc error time format
	with function planner_time()
	
	:returns: planner log file name where finding timestamp equal wmsmc error time.

	"""
	path_to_plnr_logs = '../planner.log'
	print planner_error_time
	args_grep = ['grep', '-rl', str(planner_error_time), path_to_plnr_logs]
	args_grep.extend(glob.glob('%s*' % path_to_plnr_logs))
	plnr_filename = subprocess.Popen(args_grep, stdout=PIPE)
#	print args_grep
	plnr_filename = plnr_filename.communicate()[0].split()
	if plnr_filename == None:
		print "Not find planner file with this timestamp, again after + 1 second"
		planner_error_time = planner_error_time + timedelta(seconds=1)
		print planner_error_time
		args_grep = ['grep', '-rl', str(planner_error_time), path_to_plnr_logs]
		args_grep.extend(glob.glob('%s*' % path_to_plnr_logs))
		plnr_filename = subprocess.Popen(args_grep, stdout=PIPE)
	#	print args_grep
		plnr_filename = plnr_filename.communicate()[0].split()
		return plnr_filename
	return plnr_filename

def search_sql_log(sql_error_time):
	"""
	Search sql_save log file, where timestamp from wmsmc_server.log
	:sql_error_time: time error converted from wmsmc error time format
	with function sql_time()

	:returns: sql_save file name where finding timstamp sql_save error time format (similar to planner format)
	"""
	path_to_sql_logs = '../sql_save.log'
	args_grep = ['grep', '-rl', str(sql_error_time), path_to_sql_logs]
	args_grep.extend(glob.glob('%s*' % path_to_sql_logs))
	sql_filename = subprocess.Popen(args_grep, stdout=PIPE)
	sql_filename = sql_filename.communicate()[0].split()
	return sql_filename

def search_sm_log(sm_error_time):
	"""
	Search solvo-sm log file, where timestamp from wmsmc_server.log
	:sm_error_time: time error converted from wmsmc error time

	:returns: solvo-sm file name where finding timstamp solvo-sm error time formt
	"""
	print "search sm log " + sm_error_time 
	path_to_sm_logs = '../watch/solvo-sm'
	args_grep = ['grep', '-rl', str(sm_error_time), path_to_sm_logs]
	print args_grep
	args_grep.extend(glob.glob('%s*' % path_to_sm_logs))
	sm_filename = subprocess.Popen(args_grep, stdout=PIPE)
	sm_filename = sm_filename.communicate()[0].split()
	if len(sm_filename) == 0:
		print "Can't find %s timestamp in solvo-sm.log, maybe log in archive or not exist" % (sm_error_time)
		sm_filename = None
	return sm_filename

def planner_time(error_time):
	"""
	Convert error timestamp in timestamp in planner log format
	like this '28-04-2022 14:19:42'

	:error_time: error timestamp in datetime object

	:returns: error timestamp as planner timestamp format in string type,
	presition to minutes.
	"""
	date_format_str = '%d-%m-%Y %H:%M:%S'
	planner_time = datetime.strftime(error_time, date_format_str)
	return planner_time

def sql_time(error_time):
	"""
	Convert error timestamp to sql_save timestamp log format, similar planner timestamp

	:error_time: error timestamp in datetime object

	:returns: error timestamp as sql_save timestamp format in string type
	"""
	date_format_str = '%d-%m-%Y %H:%M:%S'
	sql_save_time = datetime.strftime(error_time, date_format_str)
	return sql_save_time	

def wmsmc_server_time(time):
	"""
	Convert input parametr error timestamp to clean wmsmc timestamp format without milliseconds and
	tread identifier.

	:time: error wmsmc log timestamp from start argument

	:returns: error time wmsmc in datetime object
	"""
	date_format_str = '%Y-%m-%dT%H:%M:%S'
	er_time_raw = time
	date_split = er_time_raw.split('T')
	date_identiefer_split = er_time_raw.split(' ')
	date_identiefer_split = date_identiefer_split[0].split('.')
	error_time = strptime(date_identiefer_split[0], date_format_str)
	return error_time

def find_b_time(before_time, logfile_name):
	counter = 1
	while counter <= 60:
		before_time = before_time - timedelta(seconds=1)
		counter = counter - 1
		sed_b_time = sed_b_time_fwmsmc(before_time)
		g_args = ['grep', sed_b_time, logfile_name]
		result_real_b_time = grep_time(g_args)
		counter += 1
		if len(result_real_b_time) != 0:
			print "Before time found, stop"
			print result_real_b_time[0], sed_b_time
			break
		else:
			print "\033[93m" + """
			WARNING!: Don't find timestamp from  %s, to %s
			in %s but not archived logs, find and cutting manual please
			""" %(sed_b_time, result_real_b_time, logfile_name)
			print '\033[0m'
	return result_real_b_time[0]
	
def find_a_time(after_time, logfile_name):
	counter = 1
	while counter <= 60:
		after_time = after_time + timedelta(seconds=counter)
		sed_a_time = sed_a_time_fwmsmc(after_time)
		g_args = ['grep', sed_a_time, logfile_name]
		result_real_a_time = grep_time(g_args)
		counter += 1
		if len(result_real_a_time) != 0:
			print "After time found , stop"
			print result_real_a_time[0], sed_a_time
			break
		else:
			print "\033[93m" + """
			WARNING!: Don't find timestamp from  %s, to %s
			in %s but not archived logs, find and cutting manual please
			""" %(sed_a_time, result_real_a_time, logfile_name)
			print '\033[0m'
			pass
			result_real_a_time = ['None']
	return result_real_a_time[0]

def find_b_time_plnr(before_time, logfile_name):
	counter = 1
	while counter <= 60:
		before_time = before_time - timedelta(seconds=counter)
		sed_b_time = sed_b_time_plnr(before_time)
		g_args = ['grep', sed_b_time, logfile_name]
		print g_args
		result_real_b_time = grep_time(g_args)
		counter += 1
		if len(result_real_b_time) != 0:
			print "Before time found, stop"
			result_real_b_time_str = result_real_b_time[0] + ' ' + result_real_b_time[1]
			print result_real_b_time_str, sed_b_time
			break
		else:
			print "\033[93m"+  """
			WARNING!: Don't find timestamp from  %s, to %s
			in planner.log but not archived logs, find and cutting manual please
			""" %(sed_b_time, result_real_b_time)
			print '\033[0m'
			print 'Sed "b" time: ', sed_b_time
	return result_real_b_time_str
	
def find_a_time_plnr(after_time, logfile_name):
	counter = 1
	while counter <= 60:
		after_time = after_time + timedelta(seconds=counter)
		sed_a_time = sed_a_time_plnr(after_time)
		g_args = ['grep', sed_a_time, logfile_name]
		result_real_a_time = grep_time(g_args)
		counter += 1
		if len(result_real_a_time) != 0:
			print "After time found , stop"
			result_real_a_time_str = result_real_a_time[0] + ' ' + result_real_a_time[1]
			print result_real_a_time_str, sed_a_time
			break
		else:
			print "\033[93m" + """
			WARNING!: Don't find timestamp from  %s, to %s
			in planner.log but not archived logs, find and cutting manual please
			""" %(sed_a_time, result_real_a_time)
			print '\033[0m'
			print 'Sed "a" time: ', sed_a_time
	return result_real_a_time_str


def find_b_time_sql(before_time, logfile_name):
	"""
	Find timestamp before error in sql filelog. If 60 try give no result,
	print Warning and stop function.

	:before_time: datatime format param calculated from error timestamp and
        several minutes early error.
	:logfile_name: name sql_save.log where finding error timestamp in function
	search_sql_log()

	:returns: real before error timestamp in sql_save.log format
	"""
	counter = 1
	while counter <= 60:
		before_time = before_time - timedelta(seconds=1)
		sed_b_time = sed_b_time_plnr(before_time)
		g_args = ['grep', sed_b_time, logfile_name]
		print g_args
		result_real_b_time = grep_time(g_args)
#		print result_real_b_time[1:3]
		counter += 1
		try:
			trimed_b_time_date = result_real_b_time[1].replace('[', '')
			trimed_b_time_time = result_real_b_time[2].replace(']', '')
			result_real_b_time_str = trimed_b_time_date + ' ' + trimed_b_time_time
		except IndexError as er:
			result_real_b_time_str = None
			print "Time not fount, try again" 
			pass
		if len(result_real_b_time) != 0:
			print "Before time found, stop"
			print result_real_b_time_str, sed_b_time
			break
		else:
			print "\033[93m" + """
			WARNING!: Don't find timestamp from  %s, to %s
			in planner.log but not archived logs, find and cutting manual please
			""" %(sed_b_time, result_real_b_time_str)
			print '\033[0m'
			print 'Sed "b" time: ', sed_b_time
	return result_real_b_time_str
	
def find_a_time_sql(after_time, logfile_name):
	"""
        Find timestamp before error in sql filelog. If 60 try give no result,
        print Warning and stop function.

        :after_time: datatime format param calculated from error timestamp and
        several minutes early error.
        :logfile_name: name sql_save.log where finding error timestamp in function
        search_sql_log()

        :returns: real before error timestamp in sql_save.log format
        """
	counter = 1
	while counter <= 60:
		after_time = after_time + timedelta(seconds=1)
		sed_a_time = sed_a_time_plnr(after_time)
		g_args = ['grep', sed_a_time, logfile_name]
		result_real_a_time = grep_time(g_args)
		print result_real_a_time[1:3]
		counter += 1
		try:
			trimed_a_time_date = result_real_a_time[1].replace('[', '')
			trimed_a_time_time = result_real_a_time[2].replace(']', '')
			result_real_a_time_str = trimed_a_time_date + ' ' + trimed_a_time_time
		except IndexError as err:
			result_real_a_time_str = None
			print "Time not found, try again"
			pass
		if len(result_real_a_time) != 0:
			print "After time found , stop"
			print result_real_a_time_str, sed_a_time
			break
		else:
			print "\033[93m" +  """
			WARNING!: Don't find timestamp from  %s, to %s
			in planner.log but not archived logs, find and cutting manual please
			""" %(sed_a_time, result_real_a_time_str)
			print "\033[0m"
			print 'Sed "a" time: ', sed_a_time
	return result_real_a_time_str


def copy_to_dual(logs_list):
	login = raw_input("Input you login on dual.solvo.ru: ")
	scp_args = 'scp %s.gz %s.gz %s.gz %s.gz %s@dual2.solvo.ru:~/' % (logs_list[0], logs_list[1], logs_list[2], logs_list[3], login)
	print scp_args
	subprocess.call(scp_args.split(" ")) 


#TODO write this search log file from params from cli, time_stamp and logfile name. Convert to function.

### Start main section ###

options, args = parser.parse_args()
logs_dir = subprocess.Popen(['pwd'], stdout=PIPE )
logs_dir = logs_dir.communicate()[0].split()
args_grep = ['grep', '-rl', options.time]
print args_grep
path_to_logs_name = '../' + str(options.log_name)
args_grep.extend(glob.glob('%s*' % path_to_logs_name))
file_name = subprocess.Popen(args_grep, stdout=PIPE)
file_name = file_name.communicate()[0].split()
print file_name

strptime = lambda date_string, format: datetime(*(time.strptime(date_string, format)[0:6]))

### wmsmc_server.log cutting sction ###

error_time = wmsmc_server_time(options.time)	

before_time = error_time - timedelta(minutes=n)
after_time = error_time + timedelta(minutes=plus_n)

print "\033[92m" + "Start cutting wmsmc_server.log" + "\033[00m"
sed_b_time = sed_b_time_fwmsmc(before_time)
sed_a_time = sed_a_time_fwmsmc(after_time)
g_args = ['grep', sed_b_time, file_name[0]]

#print g_args

result = grep_time(g_args)

sed_b_time_plnr_ =  sed_b_time_plnr(before_time)
sed_a_time_plnr_ =  sed_a_time_plnr(after_time)


#before_time = error_time - timedelta(minutes=n)
#after_time = error_time + timedelta(minutes=plus_n)


result_real_b_time = find_b_time(before_time, file_name[0])
result_real_a_time = find_a_time(after_time, file_name[0])

wmsmc_server_write_result = sed_and_write(result_real_b_time, result_real_a_time, file_name[0])
print "\033[92m" +  "Data wmsmc_server.log is collected in file: ", wmsmc_server_write_result + "\033[00m"

### Planner cutting section ###

print "\033[92m" +  "Started cutting planner.log" + "\033[00m"
plannertime_search_str = '%d-%m-%Y %H:%M'
plannertime_search = datetime.strftime(error_time, plannertime_search_str)
planner_file_name = search_planner_log(plannertime_search)

print planner_file_name

result_real_b_time_plnr = find_b_time_plnr(before_time, planner_file_name[0])
result_real_a_time_plnr = find_a_time_plnr(after_time, planner_file_name[0])

print "\033[92m" +  "Planner real b and a time:", result_real_b_time_plnr, result_real_a_time_plnr + "\033[00m"

planner_write_result = sed_and_write(result_real_b_time_plnr, result_real_a_time_plnr, planner_file_name[0])

### End Planner cutting section###

### Start SQL save cutting section ###
print "\033[92m" +  "Started cutting sql_save.log" + "\033[00m"
sql_save_search_srt = '%d-%m-%Y %H:%M'
sql_savetime_search = datetime.strftime(error_time, sql_save_search_srt)
sql_file_name = search_sql_log(sql_savetime_search)

result_real_b_time_sql = find_b_time_sql(before_time, sql_file_name[0])
result_real_a_time_sql = find_a_time_sql(after_time, sql_file_name[0])

sql_write_result = sed_and_write(result_real_b_time_sql, result_real_a_time_sql, sql_file_name[0]) 

### End SQL save cutting section ###


### Start solvo-sm cutting section ###
print "\033[92m" +  "Started cutting solvo-sm.log" + "\033[00m"
sm_search_str = '%Y-%m-%dT%H:%M'
sm_time_for_search = datetime.strftime(error_time, sm_search_str)
sm_file_name = search_sm_log(sm_time_for_search)
print sm_file_name
if sm_file_name == None:
	copy_to_dual(sql_write_result, planner_write_result, wmsmc_server_write_result, None)
	print "Bye"
	sys.exit()

relust_real_b_time_sm = find_b_time(before_time, sm_file_name[0])
relust_real_a_time_sm = find_a_time(after_time, sm_file_name[0])

print sm_file_name
sm_write_result = sed_and_write(relust_real_b_time_sm, relust_real_a_time_sm, sm_file_name[0])
copy_to_dual([sql_write_result, planner_write_result, wmsmc_server_write_result, sm_write_result])

print "\033[95m" + "Good job commaner!" + "\033[00m"
