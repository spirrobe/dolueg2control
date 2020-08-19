# dolueg2control
Control of dataflow for dolueg

This will depend a lot on your particular solution of data storage. 

First a word about the general procedure for our pipeline from stationdata to database in relation to the control:
1. We collect data with Campbell Scientifics Loggernet, i.e. Status Monitor and store them into "loggerfiles"
2. To transfer these data into SQL tables, we use calibration files (calfiles for short). These contain information about which columns should be taken, which ranges for values are reasonable and how values might need to be adjusted/transformed. These calfiles are the centerpiece of the control as they contain which data is written to the databsae.
3. Our control relies on the calfiles to find the datafile and then check modification date of the file, read the data and check for the newest record in the file and finally with the calfiles check the contained time-series code (not all columns are necessarily transfered into the database) for the most recent value

This means dataflow is checked at three points, which is then listed as in the example below, where each check serves to understand at which stage something might have gone wrong.
![Example of dataflow control](https://raw.githubusercontent.com/spirrobe/dolueg2control/master/control.png "Example of dataflow control")

If any of the checkpoints/column are colored yellow-black striped, this means a warning, i.e. something did not work once and can work the next time. Possibly internet connectivity of a station was lost or similar. This might resolve itself the next day, or not.
If not, the checkpoint/column turns red-black striped. This means something has gone wrong for too long and likely manual fixing is requiring.
If either of the two colorcodes applies, it is important to know where to fix problems:
- Only the last column is red//yellow means one or more time-series have not been written to the database. This indicates most likely that the specific time-series has missing values or similar, possibly due to a sensor/device breaking. Investigate the datafile. Other possibilities are that either the process is not running (computer off), stopped working due to some changes (change in code) or changes in the database block new data.
- The middle column is red/yellow means generally that there is an issue writing to the datafile. This is most likely the case when connection to the station was intermittent and data has not been updated yet in the datafile. Other options are that the datafile has moved, storage is full or similar.
- The first column represents connectivity of the station. In case it is red/yellow, the best course of action is to try a manual connection and retrieve data. If this does not work, usually fixing the stations connection is required in person.

All of this information helps to find problems and is vital to know where to start.

# calfiles

# control






