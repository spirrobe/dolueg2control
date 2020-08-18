# dolueg2control
Control of dataflow for dolueg

This will depend a lot on your particular solution of data storage. 

First a word about the general procedure for our pipeline from stationdata to database:
1. We collect data with Campbell Scientifics Loggernet, i.e. Status Monitor and store them into "loggerfiles"
2. To transfer these data into SQL tables, we use calibration files (calfiles for short). These contain information about which columns should be taken, which ranges for values are reasonable and how values might need to be adjusted/transformed.
