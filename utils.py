#!/usr/local/sci/bin/python2.7
'''
:author: yaswant.pradhan
:copyright: Crown copyright. Met Office.
'''

import  os, \
        csv, \
        glob, \
        errno, \
        math
import numpy as np
from datetime import datetime as dt


def mkdirp(directory):
    '''Make parent directories as needed, no error if existing
    :param dir: (str) directory (tree) to create
    '''
    try:
        os.makedirs(directory)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise e
        pass


def symlinkf(fsrc, fdst):
    '''Create a symbolic link pointing to fsrc named fdst.
    This is a os.symlink wrapper which removes existing destination files

    Availability: Unix.

    :param fsrc: (str) source filename
    :param fdst: (str) link filename
    '''
    try:
        os.symlink(fsrc, fdst)
    except OSError, e:
        if e.errno == errno.EEXIST:
            os.remove(fdst)
            os.symlink(fsrc, fdst)


def purge(dsrc, ext):
    '''Delete all files with matching extension in a directory

    :param dsrc: (str) source directory
    :param ext: (str) matching file extension
    '''
    exts = '*' + str(ext).strip()
    for f in glob.glob(os.path.join(dsrc, exts)):
        os.remove(f)


def dt2yjd(date=None):
    '''Converts date string in YYYYmmdd form to Year/day=of-year in YYYY/jjj
    form.
    :param date: (str) Date in YYYYmmdd. This argument overrides self.date value
    '''
    if date is None: date = dt.utcnow().strftime('%Y%m%d')
    dtobj = dt.strptime(date, '%Y%m%d')
    return(dtobj.strftime('%Y/%j'))


def yjd2dt(yjd, fmt='%Y%j'):
    '''Converts date string in YYYY/jjj to datetime object
    :param yjd: (str) Year and day-of-year in yyyyddd form
    '''
    return dt.strptime(yjd, fmt).date()


def nearest(array, value, location=False):
    '''Returns the nearest value in an array

    Args:
     * array (in, array) search array from which the nearest value to be found
     * value (in, scalar) to search

    Returns:
     * index, value (out) tuple index or position of the value in the array and the actual value in the array if location set to True, otherwise returns the closest value.

    Revisions:
    2015-06-10. Yaswant Pradhan. Initial version.
    '''
    inarray = np.asarray(array)
    loc = (np.abs(inarray - value)).argmin()
    if location == True:
        return (loc, inarray[loc])
    else:
        return inarray[loc]


def locate(array, value, epsilon=1.0):
    '''Locate the index of a value in an array.'''
    inarray = np.asanyarray(array, dtype=array.dtype)
    loc = (np.abs(value - inarray)).argmin()
    if np.abs(value - inarray[loc]) < epsilon:
        return loc
    else:
        return -1


def v_locate(array, value):
    '''v_locate function finds the intervals within a given monotonic vector
    that brackets a given set of one value. Much faster than locate when the
    array is sorted (or monotonically increasing).
    '''
    idx = np.searchsorted(array, value, side="left")
    if math.fabs(value - array[idx - 1]) < math.fabs(value - array[idx]):
        return idx - 1  # array[idx - 1]
    else:
        return idx  # array[idx]


def write_csv(filename, data=None, header=None, append=False):
    mode = 'ab' if append is True else 'wb'
    with open(filename, mode) as fp:
        writer = csv.writer(fp)
        # write header row
        if append is False:
            try:
                writer.writerow(header)
            except:
                print 'No header.'
        # write row row(s)
        try:
            writer.writerow(data)
        except:
            print "No data."



def doy(year=None, month=None, day=None):
    '''Calculate serial day of year
    '''
    from datetime import date
    if day is not None and month is not None and year is not None:
        dt = date(year, month, day)
        return dt.timetuple().tm_yday
    else:
        return date.today().timetuple().tm_yday

def aot2vis(aot):
    # AOD to Visibility (using Koschmieder's equation)
    #
    #   Vis = (1/aot) * ln(abs(C0/eps))
    #   C0 = inherent contracst of the object ~0.02
    #   eps = liminal/inherent theoretical contrast of 'black object' -1
    #
    # This formula is widely used, especially for its simplicity, and it's
    # main assumptions for its derivation are:
    # (1) The extinction coefficient is constant along the  path of sight (this
    # also means a horizontal path of sight and neglecting the curvature of the
    # earth).
    # (2) The amount of light scattered by a volume element is proportional to
    # its volume and the extinction coefficient, and also is constant along the
    # path of sight.
    # (3) The target is absolutely black, with the horizon as background.
    # (4) The eye has a contrast threshold of 0.02.
    #
    return 3.912 / aot


def aot2pm25(aot, H, S):
    # AOD and PM2.5 relationship (Hoff and Christopher, 2009)
    # AOT = PM2.5*H*S
    # H: the height of the well-mixed planetary boundary layer (PBL) and
    # S: is the specific extinction efficiency of the aerosol at the ambient
    # relative humidity.
    return aot / (H * S)


def doy2ymd(year, dayofyear):
    import datetime as dt
    return dt.datetime(year, 1, 1) + dt.timedelta(dayofyear - 1)

# # Distance
def ft2m(feet):
    '''Converts value from feet to metres'''
    return feet * 0.3048

def ft2km(feet):
    '''Converts value from feet to kilometres'''
    return feet * 0.3048 / 1e3

def km2ft(km):
    '''Converts value from kilometres to feet'''
    return km * 1e3 / 0.3048

# # Light
def freq2wl(freq):
    '''Converts frequency (cm-1) to wavelength (microns)'''
    return 1e4 / freq

def wl2freq(wl):
    '''Converts wavelength (microns) to frequency (cm-1)'''
    return 1e4 / wl

# # Mass
def kg2lb(kg):
    '''Converts value from kilograms to pounds'''
    return kg * 2.20462262

def lb2kg(lb):
    '''Converts value from pounds to kilograms'''
    return lb / 2.20462262

# # Speed
def kt2mph(kt):
    '''Converts value from knots to miles/hour'''
    return kt * 1.15077945

def mph2kt(mph):
    '''Converts value from  miles/hour to knots'''
    return mph / 1.15077945

# # Temperature
def c2f(t):
    '''Converts value from Celcius to Farenheit'''
    return t * 1.8 + 32

def f2c(f):
    '''Converts value from Farenheit to Celcius'''
    return (f - 32) / 1.8
