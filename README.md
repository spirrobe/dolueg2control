# dolueg2control
Control of dataflow for dolueg2

This will depend a lot on your particular solution of data storage. We provided some files and a bit of help here. Given the various possibilites of storing data in different form, no single fit-all solution can be provided.

First a word about the general procedure for our pipeline from stationdata to database in relation to the control:
1. We collect data with Campbell Scientifics Loggernet, i.e. Status Monitor and store them into "loggerfiles"
2. To transfer these data into SQL tables, we use calibration files (calfiles for short). These contain information about which columns should be taken, which ranges for values are reasonable and how values might need to be adjusted/transformed. These calfiles are the centerpiece of the control as they contain which data is written to the databsae.
3. Our control relies on the calfiles to find the datafile and then check modification date of the file, read the data and check for the newest record in the file and finally with the calfiles check the contained time-series code (not all columns are necessarily transfered into the database) for the most recent value


## Meaning of columns
This means dataflow is checked at three points, which is then listed as in the example below, where each check serves to understand at which stage something might have gone wrong.
![Example of dataflow control](https://raw.githubusercontent.com/spirrobe/dolueg2control/master/control.png "Example of dataflow control")

If any of the checkpoints/column are colored yellow-black striped, this means a warning, i.e. something did not work once and can work the next time. Possibly internet connectivity of a station was lost or similar. This might resolve itself the next day, or not.
If not, the checkpoint/column turns red-black striped. This means something has gone wrong for too long and likely manual fixing is requiring.
If either of the two colorcodes applies, it is important to know where to fix problems:
- Only the last column is red//yellow means one or more time-series have not been written to the database. This indicates most likely that the specific time-series has missing values or similar, possibly due to a sensor/device breaking. Investigate the datafile. Other possibilities are that either the process is not running (computer off), stopped working due to some changes (change in code) or changes in the database block new data.
- The middle column is red/yellow means generally that there is an issue writing to the datafile. This is most likely the case when connection to the station was intermittent and data has not been updated yet in the datafile. Other options are that the datafile has moved, storage is full or similar.
- The first column represents connectivity of the station. In case it is red/yellow, the best course of action is to try a manual connection and retrieve data. If this does not work, usually fixing the stations connection is required in person.

All of this information helps to find problems and is vital to know where to start.

## Meaning of tableheader
**If the whole header is yellow/red, this means the process for creating control is broken**
This can mean that the connectivity to the webserver is broken, or something is amiss with the computer/process creating the control (think change in code/password for database access or similar). This largely depends on your dataflow solution and thus no advice for fixing can be given here.


# calfiles and read_cal2
Calfiles are rather simplistic textfiles with a fixed structure. Yet they allow scaling of data, change of columns for a timeperiod or completely and in the most advanced case the application of whole functions on data as they are evaluated by a programming language. Suffice to say they and the programm to apply would need another lengthy explanation that falls outside the scope here. Instead we give a short example of how one looks and explain what it is used for.
```
ID       = ID of station (can be duplicate of station)
STATION  = Name of station (appears in control)
DEVICE   = The device used to log data (irrelevant here)
DATAFILE = Filelocation (point to the datafile containing measurement data)
STATUS   = Is the station active? (either 0 or 1 where 0 results in being skipped for control)
DT       = The interval between records in minutes of data (e.g. 1 = 1 minute, 10 = 10 minutes etc)
TIMEZONE = Timezone in which the data are stored. This can be used to move the data to a different timezone when writing to database. Primary use here is to correct for local computer timezone versus data timezone
DATABASE = Database in which the data will be stored (irrelevant here)
GENERATED = Date and name of who created this file (irrelevant here)

*CODE1  "Wind speed at height 30"
{10.09.2017 - 10.09.2018 } {CH=3} {NO=SODAR} {SCA=NONE} {RANGE=NONE} {CLIP=NONE}
{10.09.2018 - *        } {CH=4} {NO=SODAR} {SCA=NONE} {RANGE=NONE} {CLIP=NONE}
*CODE2  "Wind speed at height 40"
{10.09.2017 - *        } {CH=5} {NO=SODAR} {SCA=CODE2*5} 
```

Relevant for control are very few parameters:
STATION -> What is written in the first column of the table
DATAFILE -> Where to check if the data is current, can contain wildcards
STATUS -> Should the file even be checked
CODE1, CODE2 -> The relevant entries for the control in this example (in reality these are more sensible codes). Each of these will be checked via the database for the last entry (we do not store non-valid data like nan or any that have been removed)

Control relies on these calfiles to figure out where and what to check. Changes must be made to adjust to your situation.

# control.py
Some changes are needed to the code in this repository. 

control.py can be found in this repository as well as our calfile reader read_cal2.py
output of control.py is a text file containing html that is preferably saved with the extension .php for easy inclusion in [dolueg2page](https://github.com/spirrobe/dolueg2page)

Mandatory input to contol.py
- outfile -> where the resulting file should be written
- caldir -> where to find the calibrationfile, can be a folder with calfiles or a single calfile

Several options are available to control the behaviour of what additional information is added in the table:
- levels -> a list of two numbers, deciding which amount in hours is consided good (less than first number), suspicious (between the two), bad (larger than second)
- calfilepattern -> pass in a calfilepattern in case you only want to match some that are present in the caldir directory
- allowintermittent -> some measurements are not always available like the cloud height and this should be reflected in the information shown on hover

read_cal2.py has no dependencies outside the standard library
control.py depends on:
- read_cal2 -> the provided reader for the cal2 files
- read_datafile, i.e. a datafile reader (which depends on the format of your datafiles; if you do have Campbell Scientific files have a look at [our Campbell Scientific Reader Repository](https://github.com/spirrobe/campbell)
- getmeta -> a Python program that gets the related meta informaton of one database code from our SQL database (needed only to check if the time-series is still meant to be running; so only the status is checked). This dependency can be removed if all codes should be checked regardless
- newestrecord -> a Python programm that connects to a SQL database (or your specific solution) and gets the newest storest record of one database code

Since the last two Python file are rather specific to how our database is organised, they are not provided here. If you are interested, contact us here.


# Automatisation
Automatisation should be simply done with your current task automatisation (be it crontab or something else). Create a file containing the import and call to control
```
control("outputfile.php",
        calfile,
        # which amount in hours is considered to be okay (up to first number)
        # which amount in hours is suspicious/warning (between first and second number)
        # which amount in hours is bad/red (greater than second number)
        levels=[13, 25], 
        )

```
