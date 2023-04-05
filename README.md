# Solvo WMS Cutlogs

## Tool for cutting WMS log for attach to bug-repotrs

#### Command Line Arguments

Example: python cutlogs.py -t "2022-06-29T18:20:18.503 140631464544000" -n wmsmc_server.log


## How it work

1. Cutlogs use linux grep for find actual log file.
2. Then convert timestamp from arguments to log format timestamp.
3. Search one minute before current timestamp and one minute after.
4. Use sed with before timestamp and aftertimestamp in log file.
5. Save cutting log in run script directory.
6. Use gzip for archivate log file.
7. After all files collect cutlogs use linux scp, for copy to you home dir on dual.

- Developing on Python 2.6.6
