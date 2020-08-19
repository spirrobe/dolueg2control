#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# """
# Created on Fri Feb 16 14:06:47 2018
#
# @author: spirro00
# """


def read_cal2(file,
              timeformat=['%d.%m.%Y',
                          '%d.%m.%Y %H:%M',
                          '%d.%m.%Y %H:%M:%S',
                          ],
              quiet=True,):

    import codecs
    import datetime

    if not file.endswith('cal2'):

        if not quiet:
            print('Wrong file given, has to end with .cal2!')
        return False

    with codecs.open(file, 'r', 'iso-8859-15') as fo:
        lines = fo.readlines()

    calibration = {}
    calibration['comments'] = []
    calibration['codes'] = {}
    calibration['meta'] = []

    ix = [len(line.strip()) for line in lines]
    ix = ix.index(0)

    callines = lines[:ix]
    for i in callines:
        if i.rstrip().startswith('#'):
            calibration['comments'].append(i)
        else:
            calibration['meta'].append(i)

    calibration['meta'] = [i.strip().split('=') for i in calibration['meta']]

    calibration['meta'] = {i[0].strip().lower(): '='.join([j.strip() for j in i[1:]])
                           if len(i) >= 2 else None # keep given keys even is they are empty
                           for i in calibration['meta']}

    calibration['meta']['datafile'] = calibration['meta']['datafile']


    datafile = calibration['meta']['datafile']
    datafile = datafile.replace('\\', '/')

    if datafile.startswith('//'):
        datafile = datafile[1:]

    calibration['meta']['datafile'] = datafile

    if 'flagfile' in calibration['meta']:
        flagfile = calibration['meta']['flagfile']
        flagfile = flagfile.replace('\\', '/')
    else:
        flagfile = None
    calibration['meta']['flagfile'] = flagfile

    lines = lines[9:]

    if 'timezone' in calibration['meta']:
        calibration['meta']['timezone'] = int(calibration['meta']['timezone'])
    else:
        print('#'*30, '\n',
              'WARNING: No timezone entry in calfiles, please fix calfile',
              file+'\n',
              'Assuming UTC to continue', '\n',
              '#'*30, '\n',)
        calibration['meta']['timezone'] = 0

    tz = datetime.timedelta(hours=calibration['meta']['timezone'])
    tz = datetime.timezone(tz)
    calibration['meta']['timezone'] = tz

    if not quiet:
        print(calibration['meta'])

    init = False

    for lineno, line in enumerate(lines):

        line = line.lstrip().rstrip()

        if line.startswith('*'):
            init = True

        elif line.startswith('#'):
            comment = line
            if not quiet:
                print('Comment:', comment)
            calibration['comments'].append(comment)
            continue

        if init:
            if line.lstrip().startswith('*'):
                if '\t' in line[1:].strip():
                    code = line[1:].strip().split('\t')
                else:
                    code = line[1:].strip().split(' ')

                if len(code) >= 2:
                     descr = code[1].replace('"', '')
                else:
                     descr = ' ' #code[1].replace('"', '')

                if not quiet:
                    print('Found entry for',
                          descr,
                          'with dbentry',
                          code)
                code = code[0]
#                calibration[code] = []

            elif line and line.rstrip().startswith('{'):

                info = line.replace('}  {', '} {').split('} {')
                timekey = info[0].strip()[1:].split(' - ')

                _ = timekey[0].strip().count(':')
                timekey[0] = datetime.datetime.strptime(timekey[0].strip(),
                                                        timeformat[_])

                if '*' not in timekey[1] and timekey[1]:
                    _ = timekey[1].strip().count(':')
                    timekey[1] = datetime.datetime.strptime(timekey[1].strip(),
                                                            timeformat[_])
                else:
                    timekey[1] = datetime.datetime.utcnow()

                timekey[1] = timekey[1].replace(tzinfo=tz)
                timekey[0] = timekey[0].replace(tzinfo=tz)

                if info[1].startswith('CH='):
                    channel = True
                    channelnumber = int(info[1][3:].split(',')[0])
                    # adapt channelnumber to a sensible format since
                    # the IDL way still includes legacy format, i.e.
                    # it has year, doy, hour as columns and
                    channelnumber -= 3
                else:
                    channel = False
                    channelnumber = -1

                channelnumber = [channelnumber]

                def floatconverter(x, quiet=True):
                    if isinstance(x, list):
                        x = [floatconverter(i) for i in x]
                    else:
                        try:
                            x = float(x)
                        except ValueError:
                            if x.lower() == 'none':
                                x = None
                            else:
                                if not quiet:
                                    print('Entry weird', x)
                                pass
                    return x

                # scaling, clipping and ranging as well as their conversion
                # to float values if approriate
                other = {}
                for i in info[1+(channelnumber[0] != -1):]:

                    what = i.split('=')
                    key = what[0]
                    what = '='.join(what[1:]).split('#')

                    if len(what)-1:
                        other['comment'] = what[-1]

                    what = what[0].rstrip()
                    what = what.rstrip('}')

                    if key != 'SCA':
                        what = what.split(',')

                    other[key] = floatconverter(what, quiet=quiet)

                # so we can add it to the rest of the list
                other = [other]

                # no channel could be found it has to be a secondary
                # i.e. its a derived measurement
                if channel:
                    if code in calibration['codes']:
                        entry = timekey + channelnumber + other
                        calibration['codes'][code].append(entry)
                    else:
                        entry = [timekey + channelnumber + other]
                        calibration['codes'][code] = entry
                else:
                    if 'secondary' not in calibration['codes']:
                        calibration['codes']['secondary'] = {}
                    if code in calibration['codes']['secondary']:
                        entry = timekey + other
                        calibration['codes']['secondary'][code].append(entry)
                    else:
                        entry = [timekey + other]
                        calibration['codes']['secondary'][code] = entry
            elif line:
                calibration['comments'].append(line)
    return calibration


if __name__ == '__main__':
    print('*'*10, 'HELP for read_cal2', '*'*10)
    print('Reads a calfile version 2 and passes back all given codes within',
          'If included also hands back comments, and secondary code',
          'derived from the first ones')

