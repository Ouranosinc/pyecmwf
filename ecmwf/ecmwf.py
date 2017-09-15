import os
import datetime
import copy

import numpy as np
import netCDF4
from ecmwfapi import ECMWFDataServer

import ecmwf_variables
import ecmwf_datasets

# Version, should be move to an __init__.py file if ever creating
# a package out of this...
__version__ = '0.1.2'

cell_methods_windows = ['sum', 'maximum', 'median', 'mid_range', 'minimum',
                        'mean', 'mode', 'standard_deviation', 'variance']


def guess_main_variable(ncdataset):
    d = 0
    for ncvar in ncdataset.variables:
        vd = len(ncdataset.variables[ncvar].shape)
        if vd > d:
            main_var = ncvar
            d = vd
    return main_var


def fetch_ecmwf_var_dict(ecmwf_var_dict, var_name, experiment=None):
    if not ecmwf_var_dict:
        if experiment == 'fc':
            ecmwf_var_dict = ecmwf_variables.ecmwf_vars_forecast[var_name]
        elif experiment == 'an':
            ecmwf_var_dict = ecmwf_variables.ecmwf_vars_analysis[var_name]
        else:
            raise NotImplementedError()
    return ecmwf_var_dict


def experiment_name(ecmwf_var_dict):
    if ecmwf_var_dict['type'] == 'fc':
        return 'forecast'
    elif ecmwf_var_dict['type'] == 'an':
        return 'analysis'
    else:
        raise NotImplementedError()


def _ecmwf_create_time_dim(nc1, nc_reference, ecmwf_var_dict):
    if nc_reference.dimensions['time'].size != 1:
        nc1.createDimension('time', nc_reference.dimensions['time'].size)
        if 'cell_methods' in ecmwf_var_dict:
            if ecmwf_var_dict['cell_methods'] != 'time: point':
                nc1.createDimension('nv', 2)


def _ecmwf_create_level_dim(nc1, nc_reference):
    if 'level' in nc_reference.dimensions:
        nc1.createDimension('level', nc_reference.dimensions['level'].size)


def _ecmwf_create_time(nc1):
    if 'time' in nc1.dimensions:
        if 'nv' in nc1.dimensions:
            time = nc1.createVariable('time', 'f4', ('time',))
        else:
            time = nc1.createVariable('time', 'i4', ('time',))
        time.axis = 'T'
        time.units = "hours since 1900-01-01 00:00:00"
        time.long_name = 'time'
        time.standard_name = 'time'
        time.calendar = 'gregorian'
        if 'nv' in nc1.dimensions:
            time.bounds = 'time_bnds'
            nc1.createVariable('time_bnds', 'f4', ('time', 'nv'))


def _ecmwf_fill_time(nc1, nc_reference, ecmwf_var_dict):
    time = nc1.variables['time']
    time_ref = nc_reference.variables['time']
    old_times = time_ref[:]
    dt = np.diff(old_times)
    if dt.min() != dt.max():
        raise NotImplementedError("Varying time interval")
    dt = dt.min()
    datetimes = netCDF4.num2date(old_times, time_ref.units, time_ref.calendar)
    new_times = netCDF4.date2num(datetimes, time.units, time.calendar)
    cell_methods = ecmwf_var_dict.get('cell_methods', '')
    if (not cell_methods) or (cell_methods == 'time: point'):
        time[:] = new_times
    else:
        time[:] = new_times - (dt / 2.0)

    if 'time_bnds' in nc1.variables:
        time_bnds = nc1.variables['time_bnds']
        time_bnds[:,0] = new_times - dt
        time_bnds[:,1] = new_times


def optimal_chunksizes(nc1):
    # Placeholder
    return (248, 61, 60)


def _ecmwf_create_var(nc1, var_name, ecmwf_var_dict):
    dims = []
    if 'time' in nc1.dimensions:
        dims.append('time')
    if 'level' in nc1.dimensions:
        dims.append('level')
    dims.extend(['lat', 'lon'])

    least_digit = ecmwf_var_dict.get('least_significant_digit', None)
    var1 = nc1.createVariable(
        var_name, 'f4', tuple(dims), zlib=True,
        chunksizes=optimal_chunksizes(nc1),
        fill_value=netCDF4.default_fillvals['f4'],
        least_significant_digit=least_digit)
    return var1


def _ecmwf_fill_var(var1, var_ref, ecmwf_var_dict):
    ref_data = var_ref[:,:,:]
    if ('accumulation' in ecmwf_var_dict) and ecmwf_var_dict['accumulation']:
        if ecmwf_var_dict['accumulation_method'] == 'mean':
            ref_data[3::4,:,:] = ref_data[3::4,:,:] - ref_data[2::4,:,:]
            ref_data[2::4,:,:] = ref_data[2::4,:,:] - ref_data[1::4,:,:]
            ref_data[1::4,:,:] = ref_data[1::4,:,:] - ref_data[0::4,:,:]
        elif ecmwf_var_dict['accumulation_method'] == 'min':
            # This is a problem... in this case the final field is not the
            # same size...
            raise NotImplementedError()
        elif ecmwf_var_dict['accumulation_method'] == 'max':
            raise NotImplementedError()
        else:
            raise NotImplementedError()
    if 'scale_factor' in ecmwf_var_dict:
        ref_data = ref_data * ecmwf_var_dict['scale_factor']
    if 'add_offset' in ecmwf_var_dict:
        ref_data = ref_data + ecmwf_var_dict['add_offset']
    if ecmwf_var_dict.get('force_positive', False):
        indices = np.where(ref_data < 0.0)
        ref_data[indices] = 0.0
    var1[:,:,:] = ref_data


def ecmwf_cf_netcdf(input_file, output_file, var_name, title, source,
                    experiment=None, ecmwf_var_dict=None):
    """ECMWF CF compliant NetCDF.

    Parameters
    ----------
    input_file : str
        This is a file obtained through a Retrieve NetCDF request on MARS.
    output_file : str
    var_name : str
    title : str
    reference : str
    source : str
    experiment : str
        either 'fc' or 'an', only used if falling back to default
        ecmwf_var_dict in ecmwf_variables.py
    ecmwf_var_dict : dict
        Dictionary containing the following keys:
        'ecmwf_name', 'ecmwf_tag': '129.128', 'standard_name', 'type',
        'cell_methods'

    """

    nc_reference = netCDF4.Dataset(input_file, 'r')
    ecmwf_var_dict = fetch_ecmwf_var_dict(ecmwf_var_dict, var_name, experiment)
    ecmwf_var_name = guess_main_variable(nc_reference)

    creation_time = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    nc1 = netCDF4.Dataset(output_file, 'w', format='NETCDF4_CLASSIC')

    nc1.Conventions = 'CF-1.7'
    nc1.title = title
    nc1.history = ("{0}\n{1} (pyecmwf-{2}): "
                   "Reformat to CF-1.7.").format(
        nc_reference.history, creation_time, __version__)
    nc1.institution = 'ECMWF'
    nc1.source = source
    nc1.experiment = experiment_name(ecmwf_var_dict)
    nc1.references = 'http://apps.ecmwf.int/datasets/'
    nc1.redistribution = "Redistribution prohibited."

    _ecmwf_create_time_dim(nc1, nc_reference, ecmwf_var_dict)
    _ecmwf_create_level_dim(nc1, nc_reference)
    nc1.createDimension('lat', nc_reference.dimensions['latitude'].size)
    nc1.createDimension('lon', nc_reference.dimensions['longitude'].size)

    _ecmwf_create_time(nc1)
    _ecmwf_fill_time(nc1, nc_reference, ecmwf_var_dict)

    if 'force_height' in ecmwf_var_dict:
        level = nc1.createVariable('height', 'f4', tuple())
        level.axis = 'Z'
        level.units = 'm'
        level.positive = 'up'
        level.long_name = 'height'
        level.standard_name = 'height'
        level[0] = ecmwf_var_dict['force_height']
    elif 'level' in nc1.dimensions:
        raise NotImplementedError()
        # Here we will have to take into account that there are multiple
        # level type supported by ECMWF
        level = nc1.createVariable('level', 'f4', ('level',))
        level.axis = 'Z'
        level.units = 'Pa'
        level.positive = 'down'
        level.long_name = 'air_pressure'
        level.standard_name = 'air_pressure'

    lat = nc1.createVariable('lat', 'f4', ('lat',))
    lat.axis = 'Y'
    lat.units = 'degrees_north'
    lat.long_name = 'latitude'
    lat.standard_name = 'latitude'
    lat[:] = nc_reference.variables['latitude'][:]

    lon = nc1.createVariable('lon', 'f4', ('lon',))
    lon.axis = 'X'
    lon.units = 'degrees_east'
    lon.long_name = 'longitude'
    lon.standard_name = 'longitude'
    lon[:] = nc_reference.variables['longitude'][:]

    var1 = _ecmwf_create_var(nc1, var_name, ecmwf_var_dict)
    var_ref = nc_reference.variables[ecmwf_var_name]
    if 'units' in ecmwf_var_dict:
        var1.units = ecmwf_var_dict['units']
    else:
        var1.units = var_ref.units.replace('*', '')
    var1.long_name = var_ref.long_name
    var1.standard_name = ecmwf_var_dict['standard_name']
    if ('cell_methods' in ecmwf_var_dict) and ecmwf_var_dict['cell_methods']:
        var1.cell_methods = ecmwf_var_dict['cell_methods']
    _ecmwf_fill_var(var1, var_ref, ecmwf_var_dict)

    nc1.close()


def download_by_year(mars_request, path_output, initial_year, final_year):
    d = copy.deepcopy(mars_request)
    server = ECMWFDataServer()
    output_files = []
    for yyyy in range(initial_year, final_year + 1):
        file_name = "{0}_{1}_{2}.nc".format(
            d['dataset'], d['param'], str(yyyy))
        d['target'] = os.path.join(path_output, file_name)
        output_files.append(d['target'])
        d['date'] = "{0}-01-01/to/{0}-12-31".format(str(yyyy))
        server.retrieve(d)
    return output_files


def download_and_convert_by_year(dataset, var_name, path_output, initial_year,
                                 final_year, title, source, experiment=None,
                                 ecmwf_var_dict=None, path_download=None,
                                 delete_mars_files=True):
    ecmwf_var_dict = fetch_ecmwf_var_dict(ecmwf_var_dict, var_name, experiment)

    if path_download is None:
        path_download = path_output

    mars_request = copy.deepcopy(ecmwf_datasets.datasets[dataset])
    mars_request['levtype'] = ecmwf_var_dict['levtype']
    mars_request['param'] = ecmwf_var_dict['ecmwf_tag']
    if ecmwf_var_dict['type'] == 'fc':
        mars_request['step'] = '3/6/9/12'
        mars_request['time'] = '00:00:00/12:00:00'
        time_frequency = '3hr'
        experiment_name = 'forecast'
    elif ecmwf_var_dict['type'] == 'an':
        mars_request['step'] = '0'
        mars_request['time'] = '00:00:00/06:00:00/12:00:00/18:00:00'
        time_frequency = '6hr'
        experiment_name = 'analysis'
    mars_request['type'] = ecmwf_var_dict['type']
    mars_request['format'] = 'netcdf'

    for yyyy in range(initial_year, final_year + 1):
        output_files = download_by_year(
            mars_request, path_download, yyyy, yyyy)
        file_name = "{0}_{1}_{2}_{3}_{4}.nc".format(
            var_name, time_frequency, dataset, experiment_name, str(yyyy))
        ecmwf_cf_netcdf(output_files[0], os.path.join(path_output, file_name),
                        var_name, title, source, experiment, ecmwf_var_dict)
        if delete_mars_files:
            os.remove(output_files[0])
