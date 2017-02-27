#!/usr/bin/env python2.7
'''
Created on 29 Jun 2015

:author: yaswant.pradhan
:copyright: Crown copyright. Met Office
'''
import sys
import numpy as np
from pyhdf.SD import SD, SDC
from pyhdf.error import HDF4Error
import h5py

#===============================================================================
# Read datasets from hdf4
#===============================================================================
class h4_parse(object):
    '''An interface to parse hdf4 file.

    Author: yaswant.pradhan
    '''

    def __init__(self, filename, **kw):
        self.filename = filename
        self.fieldnames = ''
        self.items = []
        self._get_fieldnames()


    def _get_fieldnames(self):
        '''Print available datasets in hdf file
        '''
        try:
            h4 = SD(self.filename, mode=SDC.READ)
            self.fieldnames = sorted(h4.datasets().keys())
            for k, v in sorted(h4.datasets().viewitems()):
                self.items.append((k, v[1]))
            h4.end()
        except HDF4Error as e:
            print "HDF4Error", e, self.filename


    def get(self, fieldnames=[]):
        '''Returns specific or all SDS in the hdf file as dictionary.
        SDS arrays can be accessed using the 'data' key. Note that no scaling
        is applied to the data in get() method (use get_scaled() to achieve
        that). However, the scaling and missing data information can be
        accessed using the following keys:
            'scale_factor'
            'add_offset'
            '_FillValue'
        '''
        if not isinstance(fieldnames, list):
            fieldnames = [fieldnames]

        try:
            # Open hdf4 interface in read mode
            h4 = SD(self.filename, mode=SDC.READ)
            sclinfo = None
            if 'Slope_and_Offset_Usage' in h4.attributes():
                sclinfo = 'Slope_and_Offset_Usage'


            if len(fieldnames) == 0:
                # Get all available field names from hdf
                fieldnames = []
                for key in sorted(h4.datasets()):
                    fieldnames.append(key)
            # Create and empty dataset dictionary with all available
            # fields fill in data from SDS
            datasets = dict.fromkeys(fieldnames, {})
            for key in datasets:
                attrs = h4.select(key).attributes()
                if sclinfo:
                    attrs[sclinfo] = h4.attributes()[sclinfo]

                datasets[key] = attrs
                datasets[key]['data'] = h4.select(key).get()
            # Close hdf interface
            h4.end()
        except HDF4Error as e:
            print "HDF4Error", e
            sys.exit(1)

        # Return un-calibrated datasets/attributes dictionary
        return datasets


    def get_scaled(self, fieldnames=[]):
        temp = self.get(fieldnames)
        scaled = dict.fromkeys(temp.keys(), None)
        fillvalue = {}

        for k in scaled:
            # see h4.attributes()['Slope_and_Offset_Usage']
            fillvalue[k] = temp[k]['_FillValue']
            scaled[k] = temp[k]['data'] * \
                        (temp[k]['scale_factor'] - temp[k]['add_offset'])

            w = np.where(temp[k]['data'] == fillvalue[k])
            scaled[k][w] = fillvalue[k]

        # Add FillValues information
        scaled['_FillValues'] = fillvalue

        # Return scaled datasets dictionary
        return scaled



#===============================================================================
# Read datasets from hdf5
#===============================================================================
class h5_parse(object):
    def __init__(self, filename, **kw):
        self._filename = filename
        self._datasets = []
        self.verbose = kw.get('verbose', False)

        self.get_fieldnames()

    def get_fieldnames(self, verbose=False):
        h5f = h5py.File(self._filename, mode='r')
        self.print_h5_struct(h5f)
        h5f.close()

    def print_h5_struct(self, h5, offset=' '):
        if isinstance(h5, h5py.File):
            if self.verbose:
                print h5.file, '(File)', h5.name
        elif isinstance(h5, h5py.Group):
            if self.verbose:
                print '(Group)', h5.name
        elif isinstance(h5, h5py.Dataset):
            self._datasets.append(h5.name)
            if self.verbose:
                print '(Dataset)', h5.name, 'len =', h5.shape
        else:
            print 'WARNING: Unknown item in HDF5 file', h5.name
            sys.exit ("Execution terminated.")

        if isinstance(h5, h5py.File) or isinstance(h5, h5py.Group):
            for key, val in dict(h5).iteritems():
                if self.verbose: print offset, key,
                self.print_h5_struct(val, offset + ' ')

    def get(self, dsetname):
        h5f = h5py.File(self._filename, mode='r')
        dataset = h5f[dsetname][:]
        h5f.close()
        return dataset


#===============================================================================
# Get a scientific dataset(s) from an HDF4 file
#===============================================================================
def get_sd(FILENAME=None, SDSNAME=None, QUIET=False):
    '''Return SDS object(s) from HDF4 file

    Kwargs:
     * FILENAME (str) Input filename
     * SDSNAME (list) List of fields to read in
     * QUIET (bool) Silent all information

    Returns:
     * SDS object or list of objects where object.get() method returns a numpy ndarray
    '''
    from ypylib import dialog

    hdf_type = [('HDF SD file', '*.hdf')]

    # Open file(s)
    fi = dialog.pickfile(filetype=hdf_type) if not FILENAME else FILENAME
    if (QUIET is False):
        print '-' * (len(fi) + 8)
        print "Opening {0}".format(fi)
        print '-' * (len(fi) + 8)


    # Open HDF SD interface
    try:
        hdf4 = SD(fi, SDC.READ)

        if not SDSNAME:
            # List all valid SDS in the file
            datalist = hdf4.datasets().keys()
            datalist.sort()
            for k in datalist: print k
            DATAFIELD_NAME = raw_input("\n>> Please type dataset name(s) to read: ")
            DATAFIELD_NAME = map(str, DATAFIELD_NAME.split())
        else:
            if type(SDSNAME) != list: SDSNAME = [SDSNAME]
            DATAFIELD_NAME = SDSNAME

        # Read in SDs
        sds = []
        for idx, val in enumerate(DATAFIELD_NAME):
            if (QUIET is False): print "Reading {0} {1} ..".format(idx, val)
            sds.append(hdf4.select(val))
            # print sds.info()

        # Return SDS object instead of list if only one dataset is requested
        if len(sds) == 1: sds = sds.pop()
        return sds

    except HDF4Error as e:
        print "HDF4Error", e
        sys.exit(1)



#===============================================================================
# Get a specific dataset from an HDF5 file
#===============================================================================
def get_h5(filename, dataset, start=[0, 0], stop=[None, None], stride=[1, 1]):
    '''
    Read a 2D dataset from HDF5 file

    Args:
     * filename (str) HDF5 filename
     * dataset (str) HDF5 dataset to read. The assumption here is that the dataset is 2 dimensional

    Kwargs:
     * start (list) [x0, y0] starting position if a sub-region is required
     * stop (list) [x0, y0] ending position if a sub-region is required
     * stride (list) [xn, yn] number of pixels to skip while returning the dataset

    Returns:
     * 2D numpy array of specified dataset (or a sliced region see Kwargs)
    '''

    print("Reading " + dataset + '..')
    f = h5py.File(filename, 'r')
    group = f['/']
    #
    # For compound (structured) dataset the slicing approach wont work as is
    # TODO: think of a clever way to deal with that, eg,
    #      data = group[dataset] and then apply slicing?
    #
    if not stop[0] or not stop[1]:
        data = np.ma.array(group[dataset][start[0]::stride[0],
                                          start[1]::stride[1]])
    else:
        data = np.ma.array(group[dataset][start[0]:stop[0]:stride[0],
                                          start[1]:stop[1]:stride[1]])

    f.close()
    return data



def get_nc(filename, dataset, verb=False):
    from netCDF4 import Dataset
    if verb: print("Reading " + dataset + '..')
    with Dataset(filename, 'r', format='NETCDF3_CLASSIC') as f:
        data = f.variables[dataset]            
        return data[:]
    


def get_nc4(filename, dataset):
    from netCDF4 import Dataset
    print("Reading " + dataset + '..')
    with Dataset(filename, 'r') as f:
        # Dataset is the class behaviour to open the
        # file and create an instance of the ncCDF4
        # class
        data = f.variables[dataset]    
        return data[:]    


#===============================================================================
# Additional Tools
#===============================================================================
def plot_sd(SD):
#     TODO:
    import matplotlib.pyplot as plt
    import matplotlib.gridspec as gridspec
    from matplotlib import ticker

    name = SD.info()[0]
    rank = SD.info()[1]
    dims = SD.info()[2]

    fill = SD._FillValue
    scale = SD.scale_factor
    offset = SD.add_offset
#     unit = SD.units
    data = SD.get()
    # print data.shape, rank
    scl_data = data * scale + offset
    vrng = np.array(SD.valid_range) * scale + offset


    if rank == 3:
        nc = 3  # number of columns in figure
        nr = dims[0] / nc + 1 if dims[0] % nc > 0 else dims[0] / nc
        fig = plt.figure(figsize=(12, nr * 3))
        gs = gridspec.GridSpec(nr, nc)

        for i in range(0, dims[0]):
            if data[i, :, :].max() == fill: continue

            ax = fig.add_subplot(gs[i])
            frame = plt.gca()
            frame.axes.get_xaxis().set_ticks([])
            frame.axes.get_yaxis().set_ticks([])
            ax.set_title('{0}:{1}'.format(name, i + 1), fontsize=10)
            mdata = np.ma.masked_where(data[i, :, :] == fill, scl_data[i, :, :])
#             print 'Reading array', i
#             print mdata.min(), mdata.max(), mdata.ptp()
            vrng = [mdata.min(), mdata.max()]
            plt.imshow(mdata.T, vmin=vrng[0], vmax=vrng[1],
                        cmap=plt.cm.Spectral_r)  # @UndefinedVariable

            cb = plt.colorbar(orientation='vertical', fraction=.03,
                              format='%0.2f')
            tick_locator = ticker.MaxNLocator(nbins=6)
            cb.locator = tick_locator
            cb.update_ticks()


    elif rank == 2:
        if data.max() == fill:
            # No valid sds in the selected field, skip further processing..
            raise SystemExit('** W: No valid data in {0} for '\
                             'plotting **\n'.format(name))
        else:
            # Create masked array of the selected field filtering out fill_values
            mdata = np.ma.masked_where(data == fill, scl_data)
            fig = plt.figure(figsize=(4, 3))
            ax = fig.add_subplot(111)
            ax.set_title(name)
            plt.imshow(mdata.T, vmin=mdata.min(), vmax=mdata.max(),
                       cmap=plt.cm.Spectral_r)  # @UndefinedVariable
            ax.set_aspect('equal')
            plt.colorbar(orientation='vertical', fraction=.03)

    fig.tight_layout()
    plt.show()

if __name__ == '__main__':
    h4file = '/data/local/fra6/MODIS_c6c5_comparison/MODIS_SCI_C6/MYD04_L2/' + \
            '2016/162/MYD04_L2.A2016162.1045.006.2016165154520.hdf'

    h5file = '/data/local/fra6/sample_data/MSG_201202151700_lite.new.h5'
    x = h5_parse(h5file).get('/Model/GM/Stash/16201/ModelData')
    print x.shape

#     print x._datasets

    # for item in x.fieldnames: print item
    # data = x.get()
    # print data
