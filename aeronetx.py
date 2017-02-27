'''
:Module: ypylib.aeronetx
:File: /net/home/h05/fra6/PyWorkspace/ypy/ypylib/aeronetx.py
Created on 20 Jan 2017 11:12:30

:author: yaswant.pradhan (fra6)
:copyright: British Crown Copyright 2017, Met Office
'''
import pandas as pd
import linecache
from HTMLParser import HTMLParser
from StringIO import StringIO


dateparse = lambda x: pd.datetime.strptime(x, "%d:%m:%Y %H:%M:%S")

class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    '''
    Strip HTML from strings
    Source: http://stackoverflow.com/questions/753052
    '''
    s = MLStripper()
    s.feed(html)
    return s.get_data()


def parse_v3_site(site, url=None):
    '''
    Check validity of a location name against AERONET database site list at
    http://aeronet.gsfc.nasa.gov/aeronet_locations.txt

    Returns tuple (boolean, dataframe) - Is site valid, All AERONET sites as a
    pandas dataframe
    '''
    import requests

    if url is None: url = 'http://aeronet.gsfc.nasa.gov/aeronet_locations.txt'
    s = requests.get(url).content
    df = pd.read_csv(StringIO(s.decode('utf-8')), skiprows=1)

    if site in list(df.Site_Name):
        return True, df
    else:
        print "'{}' not found in AERONET Database Site List".format(site)
        return False, df



def downlaod_v3_site(site, ymd=None, ymd2=None, prd='SDA15', avg='10',
                     verb=False):
    '''
    ** Requires curl **
    site (str) AERONET location name.
    ymd, ymd2 (YYYYmmdd) default is for current date - 1.
    prd (str)
        AOD10    Aerosol Optical Depth Level 1.0
        AOD15    Aerosol Optical Depth Level 1.5
        AOD20    Aerosol Optical Depth Level 2.0
        SDA10    SDA Retrieval Level 1.0
        SDA15    SDA Retrieval Level 1.5 (default)
        SDA20    SDA Retrieval Level 2.0
        TOT10    Total Optical Depth based on AOD Level 1.0 (all points only)
        TOT15    Total Optical Depth based on AOD Level 1.5 (all points only)
        TOT20    Total Optical Depth based on AOD Level 2.0 (all points only)
    avg (in) Data Format:
        For All points = 10 (default)
        For Daily average = 20
    '''
    import os, tempfile
    from datetime import datetime, timedelta

    # Parse AERONET site first
    if not parse_v3_site(site)[0]: return

    host = 'http://aeronet.gsfc.nasa.gov/cgi-bin/print_web_data_v3'
    if ymd is None: date1 = datetime.utcnow() - timedelta(days=1)
    else: date1 = datetime.strptime(ymd, '%Y%m%d')

    y1 = date1.year
    m1 = date1.month
    d1 = date1.day
    if ymd2 is None:
        y2, m2, d2 = y1, m1, d1
        q = "curl -s -X GET '{}?site={}&year={}&month={}&day={}&{}=1&AVG={}'"
        cmd = q.format(host, site, y1, m1, d1, prd, avg)
    else:
        date2 = datetime.strptime(ymd2, '%Y%m%d')
        y2 = date2.year
        m2 = date2.month
        d2 = date2.day
        q = "curl -s -X GET '{}?site={}&year={}&month={}&day={}" + \
            "&year2={}&month2={}&day2={}&{}=1&AVG={}'"
        cmd = q.format(host, site, y1, m1, d1, y2, m2, d2, prd, avg)

    if verb: print cmd
    tmp = next(tempfile._get_candidate_names())
    os.system(cmd + ' > ' + tmp)

    with open(tmp) as f:
        html = f.read()
        os.remove(tmp)
        return strip_tags(html)


def downlaod_v3_region(llyx, uryx, ymd=None, ymd2=None,
                       prd='SDA15', avg='10'):
    '''
    ** Requires curl **
    llyx Lower-Left (Latitude, Longitude) limits for region extraction
    uryx Upper-Right (Latitude, Longitude) limits for region extraction
    ymd, ymd2 (YYYYmmdd) Date range to extract.
        default is for current date - 1.
    prd (str)
        AOD10    Aerosol Optical Depth Level 1.0
        AOD15    Aerosol Optical Depth Level 1.5
        AOD20    Aerosol Optical Depth Level 2.0
        SDA10    SDA Retrieval Level 1.0
        SDA15    SDA Retrieval Level 1.5 (default)
        SDA20    SDA Retrieval Level 2.0
        TOT10    Total Optical Depth based on AOD Level 1.0 (all points only)
        TOT15    Total Optical Depth based on AOD Level 1.5 (all points only)
        TOT20    Total Optical Depth based on AOD Level 2.0 (all points only)
    avg (in) Data Format:
        For All points = 10 (default)
        For Daily average = 20
    '''
    import os, tempfile
    from datetime import datetime, timedelta

    host = 'http://aeronet.gsfc.nasa.gov/cgi-bin/print_web_data_v3'
    if ymd is None: date1 = datetime.utcnow() - timedelta(days=1)
    else: date1 = datetime.strptime(ymd, '%Y%m%d')

    y1 = date1.year
    m1 = date1.month
    d1 = date1.day
    if ymd2 is None:
        y2, m2, d2 = y1, m1, d1
        q = "curl -s -X GET '{}?lat1={}&lon1={}&lat2={}&lon2={}" + \
            "&year={}&month={}&day={}&{}=1&AVG={}'"
        cmd = q.format(host, llyx[0], llyx[1], uryx[0], uryx[1],
                       y1, m1, d1, prd, avg)
    else:
        date2 = datetime.strptime(ymd2, '%Y%m%d')
        y2 = date2.year
        m2 = date2.month
        d2 = date2.day
        q = "curl -s -X GET '{}?lat1={}&lon1={}&lat2={}&lon2={}" + \
            "&year={}&month={}&day={}" + \
            "&year2={}&month2={}&day2={}&{}=1&AVG={}'"
        cmd = q.format(host, llyx[0], llyx[1], uryx[0], uryx[1],
                       y1, m1, d1, y2, m2, d2, prd, avg)

    tmp = next(tempfile._get_candidate_names())
    os.system(cmd + ' > ' + tmp)
    with open(tmp) as f:
        html = f.read()
        os.remove(tmp)
        return strip_tags(html)


def read_data(filename, version=2):
    '''AERONET extractor
    Read a given AERONET AOT data file, and return it as a data-frame.

    This returns a DataFrame containing the AERONET data, with the index
    set to the time-stamp of the AERONET observations. Rows or columns
    consisting entirely of missing data are removed. All other columns
    are left as-is.

    Note: there is a column offset in AERONET Version-3 total AOD files, which
    has been reported to the AERONET web database team, so I wont use any
    hacks to deal with the staggered columns at >=Optical_Air_Mass.
    '''
    # identify Aeronet product name
    fileinfo = linecache.getlines(filename)[0:7]
    for line in fileinfo:
        if 'Version' in line:
            prodname = str.strip(line)
    print prodname

#     dateparse = lambda x: pd.datetime.strptime(x, "%d:%m:%Y %H:%M:%S")
    if version == 2:
        skipr = 4
        na = 'N/A'
        renameCol = 'Last_Processing_Date(dd/mm/yyyy)'
        df = pd.read_csv(filename, skiprows=skipr, na_values=[na], \
                         parse_dates={'times':[0, 1]}, \
                         date_parser=dateparse)

    elif version == 3:  # read version 3 data
        skipr = 6
        na = -999.0
        renameCol = 'Last_Date_Processed)'

        # read actual header in the Aeronet file
        # add extra column to header so that V3 ragged dataset (ie without
        # headers) can be read correctly as data frame
        hdr = (pd.read_csv(filename, skiprows=skipr, nrows=0)).columns.tolist()

        #----------------------------------------------------------------------
        #         temporary patch for SDA files (*.ONEILL_lev15)
        #----------------------------------------------------------------------
#         if prodname == 'Version 3: SDA Retrieval Level 1.5':
#             print 'Applying column-shift patch to ' + prodname
#             hdr_list.insert(hdr_list.index('Air_Mass'), 'Dummy')
        #----------------------------------------------------------------------
        #         temporary patch for total AOD component files (*.tot_lev15)
        #----------------------------------------------------------------------
#         if prodname == 'Version 3: Total Optical Depth based on AOD Level 1.5':
#             print 'Applying column-shift patch to ' + prodname
#             hdr_list.insert(hdr_list.index('Optical_Air_Mass'), 'Dummy')
        #----------------------------------------------------------------------

        # update header with dummy wavelength columns
        hdr[-1] = 'w1'
        hdr.extend(['w' + x for x in map(str, range(2, 11))])
        # hdr_list.extend(['w2', 'w3', 'w4', 'w5', 'w6', 'w7', 'w8', 'w9'])

        # read values into data frame
        df = pd.read_csv(filename, skiprows=skipr + 1, names=hdr,
                         na_values=[na], parse_dates={'times':[0, 1]},
                         date_parser=dateparse)
    else:
        pass

    df = df.set_index('times')
    # del df['Julian_Day']

    # Drop any rows that are all NaN and any columns that are all NaN and then
    # sort by the index
    an = (df.dropna(axis=1, how='all').dropna(axis=0, how='all')
            .rename(columns={renameCol: 'Last_Processing_Date'})
            .sort_index())

    return an


def plot_v3_site_sda(site, ymd=None, ymd2=None, prd='SDA15', avg='10',
                     hourly=False, verb=False):
    import math
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        import matplotlib.pyplot as plt
        import matplotlib.dates as dates

    # Parse AERONET site first
    if not parse_v3_site(site)[0]: return

    skipr = 6
    data = downlaod_v3_site(site, ymd=ymd, ymd2=ymd2, prd=prd, avg=avg,
                            verb=verb)
    if len(data) < 100:
        print '** No data found for {} on {} **'.format(site, ymd)
        return

    hdr = pd.read_csv(StringIO(data), skiprows=skipr, nrows=1).columns.tolist()
    hdr[-1] = 'w1'
    hdr.extend(['w' + x for x in map(str, range(2, 11))])

    # read values into data frame
    df = pd.read_csv(StringIO(data), skiprows=skipr + 1, names=hdr,
                     na_values=[-999.0], parse_dates={'times':[1, 2]},
                     date_parser=dateparse)
    df = df.set_index('times')
    sda = (df.dropna(axis=1, how='all').dropna(axis=0, how='all').sort_index())

    # print sda.columns
    lat = sda['Site_Latitude(Degrees)'][0]
    lon = sda['Site_Longitude(Degrees)'][0]
    elvs = 'Alt: {:.0f}m'.format(sda['Site_Elevation(m)'][0])
    instr = 'Id: ' + str(sda['AERONET_Instrument_Number'][0])

    lats = '{:.3f}$^\circ$N'.format(lat) if lat >= 0 else '{:.3f}$^\circ$S'.\
            format(math.fabs(lat))
    lons = '{:.3f}$^\circ$E'.format(lon) if lon >= 0 else '{:.3f}$^\circ$W'.\
            format(math.fabs(lon))

    # Start plot
    pdf = sda[['Total_AOD_500nm[tau_a]',
               'Fine_Mode_AOD_500nm[tau_f]',
               'Coarse_Mode_AOD_500nm[tau_c]']]
    del df, sda

    # Hourly average?
    if hourly is True:
        dfh = pdf.resample("H", how='mean', loffset='30Min')
        dfs = pdf.resample("H", how='std', loffset='30Min')
        # print pdfs
        df = dfh
        obs = r'(hourly avg $\pm1\sigma$)'
    else:
        df = pdf
        obs = '(all points)'

    if prd == 'SDA10': lev = '1.0'
    elif prd == 'SDA15': lev = '1.5'
    elif prd == 'SDA20': lev = '2.0'
    else: lev = ''

    #----------------------------------------------------- get series statistics
    st = df.describe()
    df.columns = [r'Total: {:.3f}; {:.3f}; {:.3f}'.\
                  format(st.loc['mean'][0], st.loc['50%'][0], st.loc['std'][0]),
                  r'Fine: {:.3f}; {:.3f}; {:.3f}'.\
                  format(st.loc['mean'][1], st.loc['50%'][1], st.loc['std'][1]),
                  r'Coarse: {:.3f}; {:.3f}; {:.3f}'.\
                  format(st.loc['mean'][2], st.loc['50%'][2], st.loc['std'][2])]
    if hourly is True: dfs.columns = df.columns
    #---------------------------------------------------------------- start plot
    fig, ax = plt.subplots(figsize=(10, 5))  # @UnusedVariable
    # at this point we could use ax = df.plot() for default chart BUT,
    # we want the chart with custom styles for each series, so:
    styles = ['g-', 'bo-', 'rD-']
    sdclr = ['g', 'b', 'r']
    lwd = [1.5, 1.5, 1.5]
    msz = [7, 7, 5]
    mwd = [1.5, 1.5, 0.2]
    for c, st, lw, mw, ms, sdc in zip(df.columns, styles, lwd, mwd, msz, sdclr):
        df[c].plot(style=st, lw=lw, ax=ax, ms=ms,
                   markeredgecolor='w', markeredgewidth=mw)
        if hourly is True:
            ax.fill_between(dfs.index, df[c] - dfs[c], df[c] + dfs[c],
                            color=sdc, alpha=0.2)
    #----------------------- format ticks and tick labels based on series length
    ax.set_xticklabels(df.index, rotation=0, ha='center')
    ax.xaxis.set_major_locator(dates.DayLocator())
    ax.xaxis.set_minor_locator(dates.HourLocator(interval=3))
    tsecs = (df.index.max() - df.index.min()).total_seconds()
    if tsecs > 180 * 86400.0:
        ax.xaxis.set_major_locator(dates.YearLocator())
        ax.xaxis.set_minor_locator(dates.MonthLocator())
    elif tsecs > 30 * 86400.0:
        ax.xaxis.set_major_locator(dates.MonthLocator())
        ax.xaxis.set_minor_locator(dates.DayLocator())
    elif tsecs < 3 * 86400.0:
        ax.xaxis.set_major_locator(dates.HourLocator(byhour=range(0, 24, 6)))
        ax.xaxis.set_minor_locator(dates.HourLocator())
    else: pass
    ax.xaxis.set_major_formatter(dates.DateFormatter('%H:%M\n%d%b%y'))
    ax.grid(True, which='major', linestyle='-', alpha=0.2)
    ax.grid(True, which='minor', linestyle='-', alpha=0.1)
    # ax.tick_params(axis='both', direction='out')
    # ax.minorticks_on()

    #------------------------------------------------ plot title and axes labels
    ax.set_title('AERONET_V3_L{} SDA {}\n{} ({}, {}, {}, {})'.\
                 format(lev, obs, site, lats, lons, elvs, instr))
    ax.set_xlabel('')
    ax.set_ylabel(r'AOD_500nm ($\tau_{500}$)')

    plt.tight_layout()
    plt.legend(loc='best', prop={'size':12})
    # plt.gcf().autofmt_xdate()
    plt.show()


if __name__ == "__main__":
    # Data download examples
    # Example 1: download V3 L15 SDA all points for Dakar station
    # x = downlaod_v3_site('Dakar', ymd='20150801',ymd2='20150831')
    # print x

    # Example 2: download V3 L15 SDA all points over a specific geo region
    # x = downlaod_v3_region([14.3,15.16],[-17.7,-15.0],
    #                        ymd='20150801',ymd2='20150831')

    # Example 3: Yesterday's data over India..
    # x = downlaod_v3_region([17.7,72.5],[27.0,90.8])
    # print x

    # Site-specific plotting examples:
    # Example 1: Plot yesterdays observation over Kanpur
    # plot_v3_site_sda('Kanpur')
    #plot_v3_site_sda('Jaipur', ymd='20170222', hourly=True)
    # plot_v3_site_sda('Kanpur', ymd='20170213', ymd2='20170216')

    # Example 2: Plot from a start date to yesterday with hourly averages:
    # plot_v3_site_sda('Kuwait_University', ymd='20170114', hourly=True)

    # plot_v3_site_sda('Capo_Verde', ymd='20150812', ymd2='20150822')

#     locs = ['Praia', 'Calhau', 'Capo_Verde',
#             'Teide', 'Izana', 'La_Laguna', 'Santa_Cruz_Tenerife']

#     for i in ['Teide', 'Izana', 'La_Laguna', 'Santa_Cruz_Tenerife']:
#         print i
#         plot_v3_site_sda(i, ymd='20150812', ymd2='20150813')

    for i in ['Praia', 'Capo_Verde']:
        print i
        plot_v3_site_sda(i, ymd='20150820', ymd2='20150821')

