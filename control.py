#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# """
# Created on %(date)s
#
# @author: %(username)s
# """


def control(outfile,  # the name of the file to be produced
            # dbdir, # the database we check
            caldir,  # where we find the calibration files
            # the numbers in hours that correspond to warning and bad levels, colors are set in the css on the page
            levels=[20, 45],
            # the calfile in case the directory contains several and only
            # one/a pattern is relevant
            calfilepattern='',
            allowintermittent=False,
            quiet=True,
            **kwargs
            ):

    import os
    import socket
    import datetime

    from read_cal2 import read_cal2
    from read_datafile import read_datafile
    from sql.util import getmeta, newestrecord 
    


    # define some basic characters
    linesep = os.linesep
    tab = "\t"

    if type(caldir) == str and caldir.endswith('.cal2'):
        calfile = os.path.basename(caldir)
        caldir = os.path.dirname(caldir)

    calfiles = [i for i in os.scandir(caldir) if calfilepattern in i and calfilext in i]

    if not calfiles:
        if not quiet:
            print('No Calfiles found!')
        return False

    calfiles = sorted(calfiles)

    header = linesep+tab+tab
    header += '<table BORDER="0" CELLPADDING="0" CELLSPACING="0" >'
    header += linesep+tab+tab+tab+'<tr BGCOLOR="#FFFFFF" COLSPAN="2">'
    header += linesep+tab+tab+tab+tab+'<td ALIGN="CENTER">'

    if len(levels) > 2:
        levels = levels[:2]

    date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

    # html-code
    # just to make it look nice use an indentationlevel of three
    # which fits nicely with the rest of dolueg2 page, adapt as needed
    indent = 3

    s = tab*indent
    s += '<tr class="datenkontrolle">'
    s += linesep
    s += tab*(indent+1)
    s += '<td class="datenkontrolle" valign="top" '

    e = '</td>' + linesep + (tab * indent) + '</tr>'

    tddel = '</td>'+linesep+(tab*(indent+1))
    tddel += '<td class="datenkontrolle checktime" >'
    coldel = '</td>' + linesep + tab*(indent+1) + '<td class="datenkontrolle '

    delh = '</td>' + linesep + tab*(indent+1) + '<td class="datenkontrolle"'
    delh += ' colspan="2" valign="top" >'

    stab = tab*(indent-1) + '<table class="datenkontrolle"'
    stab += ' border="1" cellpadding="2"'
    stab += ' style="border: 1px #dddddd;" '
    stab += 'data-good="' + str(levels[0]) + '" data-bad="'
    stab += str(levels[1]) + '">'

    etab = tab*(indent-1) + '</table>'
    timetag = tab*(indent) + '<tr class="datenkontrolle creationheader">\n'
    timetag += tab * (indent+1) + '<td colspan="7">Status control time: '
    timetag += date + '</td>\n'
    timetag += tab*(indent) + '</tr>'

    c_class = ['good', 'warn', 'bad']
    head = ['Station',
            'Datatransfer',
            'Timestamp in datafile',
            'Timestamp of last database entry']

    lines = []

#    now = time.localtime()#datetime.datetime.now()
#    now = datetime.datetime.now(datetime.timezone.utc).astimezone()
    now = datetime.datetime.now(datetime.timezone.utc).astimezone()
    nownotz = now.replace(tzinfo=None)
    localtz = datetime.datetime.now(datetime.timezone.utc).astimezone()
    localtz = localtz.tzinfo

    for calfileno, calfile in enumerate(calfiles):
        if not quiet:
            print('Reading calfile:',  calfile)

        calib = read_cal2(calfile)

        # there has to be a timezone given in the calib file otherwise
        # its misformed. read_cal2 assumes UTC if not found and prints
        # a warning. Since this is for control only, this is not as crucial
        # as in the putdata
        datatimezone = calib['meta']['timezone']

        # ensure it
        if isinstance(datatimezone, datetime.timezone):
            pass
        else:
            datatimezone = datetime.timezone(datetime.timedelta(hours=int(datatimezone)))

        codes = sorted(calib['codes'].keys())

        if 'secondary' in codes:
            codes.pop(codes.index('secondary'))
            codes.extend(sorted(calib['codes']['secondary'].keys()))

        if calib['meta']['status'] not in ['1', 1]:

            if not quiet:
                print('Skipping', calfile,
                      'as status is zero, indicating station',
                      'is no longer operational')
            continue

        sqldb = None
        if 'database' in calib['meta'] and calib['meta']['database']:
            sqldb = calib['meta']['database']

        meta = getmeta(codes=codes, sqldb=sqldb, quiet=quiet)

        if not meta:
            if not quiet:
                print('No codes have been found that have fitting meta',
                      ' information, please correct the database as data',
                      ' without proper meta information are worthless')
            continue
        else:
            codes = sorted(meta.keys())
            # only keep actual codes (also kicks out jtime)
            codes = [code
                     for code in codes
                     if meta[code] and meta[code]['status']]
        if codes:
            pass
        else:
            continue

        # reset default values
        fidate, logdate, dbdate = '-'*3
        fijul, logjul = '-' * 2
        fidelay, logdelay, dbdelay, dbjul = '-' * 4
        ficol, logcol, dbcol = [c_class[2]] * 3

        datafile = calib['meta']['datafile']

        if os.path.exists(datafile):
            pass
        else:
            print(datafile, 'not found/not existing. Skipped')
            continue

        if type(datafile) == str:
            datafile = [datafile]

        shouldbedatafiles = datafile.copy()
        datafile = [i for i in datafile if os.path.exists(i)]

        # get the information about transfer of the file but nothing else yet
        if not datafile:
            ficol = c_class[2]
            fidelay = 'N/A'
        else:
            if type(datafile) == str:
                datafile = [datafile]

            mtimes = [os.path.getmtime(i) for i in datafile]
            file_time = datetime.datetime.fromtimestamp(max(mtimes))

            fidelay = (nownotz - file_time).total_seconds()
            fidelay = fidelay / 60 / 60
            fidate = file_time.strftime('%Y-%m-%d %H:%M')

            if fidelay <= levels[0]:
                ficol = c_class[0]
            elif fidelay > levels[1]:
                ficol = c_class[2]
            else:
                ficol = c_class[1]

            if fidelay >= 96:
                fidelay = '&gt; 96 H'
            else:
                fidelay = str(round(fidelay, 1)) + "H"

        # now check the data in the file according to the last timestamp
        # and add the timezone that we got from the calfile
        if not datafile:
            logcol = c_class[2]
            logdelay = 'N/A'
        else:
            if len(datafile) >= 3:
                datafile = sorted(datafile, key=os.path.getmtime)[-3:]

            if not quiet:
                print('Reading datafile:', datafile)

            if type(datafile) == list:
                extchk = datafile[0]
            else:
                extchk = datafile

            data = read_datafile(datafile,
                                 #asdataframe=True,
                                 #nlines=-150,
                                 quiet=quiet)

            if data is False:
                logcol = c_class[2]
                logdelay = 'N/A'
            else:
                # set the timezone to the one from the calibfile and then convert
                # it to the localtimezone so the offset is similar
                if data.index.tzinfo is None:
                    data = data.tz_localize(datatimezone)

                data = data.tz_convert(localtz)

                data = data.dropna(how='all')

                lastrec = max(data.index).to_pydatetime()

                logdate = lastrec.strftime("%Y-%m-%d %H:%M")

                logdelay = (now - lastrec).total_seconds()
                logdelay = logdelay / 60 / 60

                if logdelay <= levels[0]:
                    logcol = c_class[0]
                elif logdelay > levels[1]:
                    logcol = c_class[2]
                else:
                    logcol = c_class[1]

                if logdelay >= 96:
                    logdelay = '&gt; 96 H'
                else:
                    logdelay = str(round(logdelay, 1))+"H"

        # now the check the corresponding codes from the databases by getting
        # the last entry that exists

        offendingcodes = 'None'
        tmax = datetime.datetime.now()
        tmax = datetime.datetime.now(datetime.timezone.utc).astimezone()

        if 'jtime' in codes:
            codes = codes[:codes.index('jtime')] + codes[:codes.index('jtime')]

        tend = newestrecord(codes, sqldb=sqldb, includetz=True)

        if False in tend:
            dbdelay = 'N/A'
            offendingcodes = [code for _t, code in zip(tend,codes) if _t is False]
        else:
            # limit the maximum time to current time so we dont have future times
            tend = [tmax if i >= tmax else i for i in tend]
            tmin = min(tend)
            dbdate = tmin.strftime("%Y-%m-%d %H:%M")

            if not quiet:
                print(tmin)
                for ii, i in enumerate(tend):
                    print(i, codes[ii])

            # get all codes that are as old as the last one
            offendingcodes = [code
                              for i, code in enumerate(codes)
                              if tend[i] == tmin]

            dbdelay = (now - tmin).total_seconds()
            dbdelay = dbdelay / 60 / 60

            if dbdelay <= levels[0]:
                dbcol = c_class[0]
            elif dbdelay > levels[1]:
                dbcol = c_class[2]
            else:
                dbcol = c_class[1]

            if dbdelay >= 96:
                dbdelay = '&gt; 96H'
            else:
                dbdelay = str(round(dbdelay, 1))+"H"

        if allowintermittent and len(codes) == len(offendingcodes):
            offendingcodes = 'intermittent dataseries, all codes at same delay: ' + ','.join(offendingcodes)
        elif allowintermittent:
            offendingcodes = 'intermittent dataseries, oldest found: ' + ','.join(offendingcodes)
        else:
            offendingcodes = 'continuos dataseries, oldest: ' + ','.join(offendingcodes)

        thisline = s + 'style="text-align:left">' + calib['meta']['station']
        thisline += tddel + fidate + coldel + ficol
        if not datafile:
            thisline += '" title="Not found:'+shouldbedatafiles[-1]+'">'
        else:
            thisline += '" title="' + datafile[-1] + '">'
        thisline += fidelay + tddel

        thisline += logdate + coldel + logcol
        thisline += '" title="' + calfile + '">'
        thisline += logdelay + tddel

        thisline += dbdate + coldel + dbcol + '" title="'
        thisline += offendingcodes + '">' + dbdelay + e

        lines.append(thisline)

    head = ['<b>'+i+'</b>' for i in head]

    # create needed directories
    if not os.path.exists(os.path.dirname(outfile)):
        os.makedirs(os.path.dirname(outfile))

    colheader = s + '>' + head[0] + delh + head[1]

    colheader += delh + head[2] + delh + head[3] + e

    # wwrite to file
    with open(outfile, 'w') as fo:
        fo.writelines([stab+'\n', timetag+'\n', colheader+'\n'])
        fo.writelines(lines)
        fo.writelines(['\n'+etab+'\n'])


if __name__ == '__main__':
    print('*'*10, 'HELP for control', '*'*10)
    print('Creates a php file for station control on the web. It contains ')
    print('information about how old datafiles are, what calibfiles has been',
          'used and which codes may be a bit too old')
    print("Example: control('C:\\dolueg2plots\\datenkontrolle\\lae.php)', 'w:\\Laeufelfingen\\prog\\calib\\', levels=[25,49]")
