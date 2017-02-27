#!/usr/local/sci/bin/python2.7
'''
Created on 29 Jun 2015

:author: fra6 (yaswant.pradhan)
:copyright: Crown copyright. Met Office
'''
import math
import numpy as np

class msg:
    '''
    Warning! The software is for use with MSG data only and will not work in
    the given implementation for Meteosat first generation data.

    Note on CFAC/LFAC and COFF/LOFF:
        The parameters CFAC/LFAC and COFF/LOFF are the scaling coefficients
        provided by the navigation record of the LRIT/HRIT header and used
        by the scaling function given in Ref [1], page 28.

        COFF/LOFF are the offsets for column and line which are basically 1856
        and 1856 for the VIS/IR channels and refer to the middle of the image
        (centre pixel). The values regarding the High Resolution Visible Channel
        (HRVis) will be made available in a later issue of this software.

        CFAC/LFAC are responsible for the image "spread" in the NS and EW
        directions. They are calculated as follows:

        CFAC = LFAC = 2**16 / delta, with
        delta = 83.84333 micro Radian (size of one VIS/IR MSG pixel)

        CFAC = LFAC =  781648343.404  1/rad for VIS/IR
        which should be rounded to the nearest integer as stated in Ref [1].

        CFAC = LFAC = 781648343  1/rad for VIS/IR

        The sign of CFAC/LFAC gives the orientation of the image.
        Negative sign give data scanned from south to north as in the
        operational scanning. Positive sign vice versa.

    Reference:
        [1] LRIT/HRIT Global Specification (CGMS 03, Issue 2.6, 12.08.1999)
        for the parameters used in the program.
    '''
    def __init__(self):
        self.SatAltitude = 42164.0  # distance from earth centre to satellite
        self.EquatRadius = 6378.169  # radius from earth centre to equator
        self.PolarRadius = 6356.5838  # radius from earth centre to pole
        self.LongitudeSsp = 0.0  # longitude of sub-satellite point
        self.ColOffset = 1856.0  # Column offset (see note above)
        self.RowOffset = 1856.0  # Line offset (see note above)
        self.CFAC = -781648343.0  # scaling coefficients (see note above)
        self.LFAC = -781648343.0  # scaling coefficients (see note above)


    def geo2pix(self, lon, lat):
        '''
        Returns the pixel column and row number of an MSG image for a
        given pair of longitude, latitude values.
        Note: calculation based on the formulae given in Ref [1]

        :param lon: (scalar) Longitude value
        :param lat: (scalar) Latitude value
        '''
        lonR = math.radians(lon)
        latR = math.radians(lat)
        # Calculate the geocentric latitude from the geographic one using
        # equations on page 24, Ref. [1]
        lat0 = math.atan(0.993243 * (math.sin(latR) / math.cos(latR)))
        # Using c_lat calculate the length form the earth centre to the
        # surface of the earth ellipsoid ;equations on page 24, Ref. [1]
        re = self.PolarRadius / math.sqrt(1 - 0.00675701 *
                                      math.cos(lat0) *
                                      math.cos(lat0))

        # Calculate the forward projection using equations on page 24, Ref. [1]
        rl = re
        r1 = self.SatAltitude - rl * math.cos(lat0) * \
             math.cos(lonR - self.LongitudeSsp)
        r2 = -rl * math.cos(lat0) * math.sin(lonR - self.LongitudeSsp)
        r3 = rl * math.sin(lat0)
        rn = math.sqrt(r1 * r1 + r2 * r2 + r3 * r3)

        #=======================================================================
        # Check for visibility, whether the point on the earth given by the
        # latitude/longitude pair is visible from the satellite or not. This
        # is given by the dot product between the vectors of:
        #  1) the point to the spacecraft,
        #  2) the point to the centre of the earth.
        # If the dot product is positive the point is visible otherwise it is
        # invisible.
        #=======================================================================
        dotprod = r1 * (rl * math.cos(lat0) *
                        math.cos(lonR - self.LongitudeSsp)) - \
                  r2 ** 2 - r3 ** 2 * ((self.EquatRadius /
                                        self.PolarRadius) ** 2)

        if dotprod < 0:
            raise ValueError('Coordinates outside of MSG view')


        # The forward projection is x and y
        xx = math.atan(-r2 / r1)
        yy = math.asin(-r3 / rn)

        #=======================================================================
        # Convert to pixel column and row using the scaling functions on
        # page 28, Ref. [1]. And finding nearest integer value for them.
        #=======================================================================
        cc = self.ColOffset + xx * 2.0 ** (-16) * self.CFAC
        ll = self.RowOffset + yy * 2.0 ** (-16) * self.LFAC
        col = int(round(cc))
        row = int(round(ll))

        return col, row


    def pix2geo(self, col, row):
        '''
        Returns the longitude and latitude value of a pixel on MSG disc
        given the column and row index of that pixel.

        :param col: (scalar) column index of MSG pixel
        :param row: (scalr) row index of MSG pixel
        '''
        # Calculate viewing angle of the satellite by use of the equation
        # on page 28, Ref [1].
        x = (2.**16) * (col - self.ColOffset) / self.CFAC
        y = (2.**16) * (row - self.RowOffset) / self.LFAC

        #=======================================================================
        # Calculate the inverse projection
        # first check for visibility, whether the pixel is located on the earth
        # surface or in space.
        # To do this calculate the argument to sqrt of "sd", which is named "sa".
        # If it is negative then the sqrt will return NaN and the pixel will be
        # located in space, otherwise all is fine and the pixel is located on
        # the earth surface.
        #=======================================================================
        sa = ((self.SatAltitude * math.cos(x) * math.cos(y)) ** 2) - \
             (math.cos(y) ** 2 + 1.006803 * math.sin(y) ** 2) * 1737121856.0

        # Now calculate the rest of the formulas using equations on
        # page 25, Ref. [1]
        sd = math.sqrt((((self.SatAltitude * math.cos(x) * math.cos(y))) ** 2) -
                       (math.cos(y) ** 2 + 1.006803 * math.sin(y) ** 2.) *
                       1737121856.0)
        sn = (self.SatAltitude * math.cos(x) * math.cos(y) - sd) / \
             (math.cos(y) ** 2. + 1.006803 * math.sin(y) ** 2)
        s1 = self.SatAltitude - sn * math.cos(x) * math.cos(y)
        s2 = sn * math.sin(x) * math.cos(y)
        s3 = -sn * math.sin(y)
        sxy = math.sqrt(s1 * s1 + s2 * s2)

        #=======================================================================
        # Using the previous calculations the inverse projection can be
        # calculated now, which means calculating the lat./long. from
        # the pixel row and column by equations on page 25, Ref [1].
        # Generate error status
        #=======================================================================
        if sa < 0:
            raise ValueError('Coordinates outside of MSG view')

        lon = math.atan(s2 / s1 + self.LongitudeSsp)
        lat = math.atan((1.006803 * s3) / sxy)
        # Convert from radians into degrees
        return math.degrees(lon), math.degrees(lat)


    def extractgeo(self, msgarray, **kw):
        tlLonLat = kw.get('tlLonLat', (0.0, 0.0))  # top-left Lon, Lat
        brLonLat = kw.get('brLonLat', (0.0, 0.0))  # bottom-right Lon, Lat
#         trLonLat = kw.get('trLonLat', (0.0, 0.0))
#         blLonLat = kw.get('blLonLat', (0.0, 0.0))

        tl = self.geo2pix(tlLonLat[0], tlLonLat[1])
        br = self.geo2pix(brLonLat[0], brLonLat[1])
#         tr = self.geo2pix(trLonLat[0], trLonLat[1])
#         bl = self.geo2pix(blLonLat[0], blLonLat[1])
        print tl, br
        pass


def shiftlon(lon, lon_0):
    """
    Returns original sequence of longitudes (in degrees) re-centred
    in the interval [lon_0-180, lon_0+180]

    Args:
     * lon (list|nparray) original longitude array in traditional range
       (-180 to 180).
     * lon_0 (scalar) centre longitude of the returned longitude array

    Returns:
     * New longitude array with lon_0 as centre
    """
    lon_shift = np.asarray(lon)
    lon_shift = np.where(lon_shift > lon_0 + 180, lon_shift - 360 , lon_shift)
    lon_shift = np.where(lon_shift < lon_0 - 180, lon_shift + 360 , lon_shift)

    return lon_shift


def wrap_lon(lon, HEMISPHERE=False):
    '''
    Converts Longitude values in an array range from [-180:180] to [0:360]
    (SPHERE) or vice-versa (HEMESPHERE).

    :param lon: (sequence) original longitude array
    :param HEMISPHERE: (bool) setting this keyword assumes original array
     ranges from 0 to 360 and therefore returned array will be in
     -180 to 180 range.
    '''
    lon = np.asarray(lon)
    if not HEMISPHERE:  # Return longitude array in -180:+180 range
        wlon = (lon + 360) % 360
    else:  # SPHERE Return longitude array in 0:360 range
        wlon = ((lon + 180) % 360) - 180
    return wlon


def ll_vec2arr(xv, yv):
    '''
    Given 1D Longitude and Latitude vectors, convert them as 2D arrays

    :param xv: (sequence) monotonically increasing x (longitude) array
    :param yv: (sequence) monotonically increasing y (latitude) array
    '''
    return np.meshgrid(xv, yv)


if __name__ == "__main__":
    lon_0 = 180
    lon = -180 + 5 * np.arange(72)
    lon_shift = shiftlon(lon, lon_0)
    print "original lon:", lon
    print " shifted lon:", lon_shift
