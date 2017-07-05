import datetime
import netCDF4

from ecmwf_variables import ecmwf_vars

# Aliases for default fill values
defi2 = netCDF4.default_fillvals['i2']
defi4 = netCDF4.default_fillvals['i4']
deff4 = netCDF4.default_fillvals['f4']


def fixed_netcdf(path_constant_field, output_file, var_name,
                 ecmwf_var_dict=None):
    """ECMWF invariant NetCDF.

    Parameters
    ----------
    path_constant_field : str
        This is a file obtained through a Retrieve NetCDF request on MARS.
    output_file : str
    var_name : str
    ecmwf_var_dict : dict
        Dictionary containing the following keys:
        'ecmwf_name', 'ecmwf_tag': '129.128', 'standard_name', 'type',
        'cell_methods'

    """

    if not ecmwf_var_dict:
        ecmwf_var_dict = ecmwf_vars[var_name]

    nc_reference = netCDF4.Dataset(path_constant_field, 'r')
    var_ref = nc_reference.variables[ecmwf_var_dict['ecmwf_name']]

    # 2.1 Filename
    #     NetCDF files should have the file name extension ".nc".
    nc_file = output_file

    now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    nc1 = netCDF4.Dataset(nc_file, 'w', format='NETCDF4_CLASSIC')

    # 2.6.1 Identification of Conventions
    nc1.Conventions = 'CF-1.6'

    # 2.6.2. Description of file contents
    nc1.title = ('ERA-Interim')
    nc1.history = "{0}: Extract variable.\n{1}".format(
        now, nc_reference.history)
    nc1.institution = 'ECMWF'
    nc1.source = 'Reanalysis'
    nc1.references = ('https://www.ecmwf.int/en/research/climate-reanalysis/'
                      'era-interim')

    # Create netCDF dimensions
    nc1.createDimension('lat', len(nc_reference.dimensions['latitude']))
    nc1.createDimension('lon', len(nc_reference.dimensions['longitude']))

    # Create netCDF variables
    # Compression parameters include:
    # zlib=True,complevel=9,least_significant_digit=1
    # Set the fill value (shown with the 'f4' default value here) using:
    # fill_value=netCDF4.default_fillvals['f4']
    # In order to also follow COARDS convention, it is suggested to enforce the
    # following rule (this is used, for example, in nctoolbox for MATLAB):
    #     Coordinate Variables:
    #     1-dimensional netCDF variables whose dimension names are identical to
    #     their variable names are regarded as "coordinate variables"
    #     (axes of the underlying grid structure of other variables defined on
    #     this dimension).

    # 4.1. Latitude Coordinate
    lat = nc1.createVariable('lat', 'f4', ('lat',), zlib=True)
    lat.axis = 'Y'
    lat.units = 'degrees_north'
    lat.long_name = 'latitude'
    lat.standard_name = 'latitude'
    lat[:] = nc_reference.variables['latitude'][:]

    # 4.2. Longitude Coordinate
    lon = nc1.createVariable('lon', 'f4', ('lon',), zlib=True)
    lon.axis = 'X'
    lon.units = 'degrees_east'
    lon.long_name = 'longitude'
    lon.standard_name = 'longitude'
    lon[:] = nc_reference.variables['longitude'][:]

    var1 = nc1.createVariable(var_name, 'f4', ('lat', 'lon'), zlib=True,
                              fill_value=deff4)
    # 3.1. Units
    if var_ref.units == '(0 - 1)':
        var1.units = '1'
    else:
        var1.units = var_ref.units.replace('*','')
    # 3.2. Long Name
    var1.long_name = var_ref.long_name
    # 3.3. Standard Name
    var1.standard_name = ecmwf_var_dict['standard_name']
    var_ref = nc_reference.variables[ecmwf_var_dict['ecmwf_name']]
    var1[:,:] = var_ref[0,:,:]

    nc_reference.close()
    nc1.close()
