# WARNING: Setting the right parameters require knowledge of how each
# variable is stored (accumulation, units, etc.). The best place to find
# this information is http://apps.ecmwf.int/codes/grib/param-db

# ecmwf_var_dict parameters:
#     ecmwf_tag : str, param value of the MARS request (e.g. '228.128')
#     standard_name : str, CF Standard Name
#     type : 'fc' (forecast) or 'an' (analysis)
#     levtype : str
#     cell_methods : str, CF Cell Methods (optional, e.g. 'time: mean')
#     accumulation : True or False (optional, default false)
#     accumulation_method : 'mean', 'min' or 'max'
#                           (required if accumulation is True)
#     scale_factor : float, occurs before add_offset, optional
#     add_offset : float, occurs after scale_factor, optional
#     force_positive : True or False, optional
#     units : str, replace the units in the original file, optional
#     least_significant_digit : int, used to reduce size of data, optinal

ecmwf_vars = {'phis': {'ecmwf_name': 'z',
                       'ecmwf_tag': '129.128',
                       'standard_name': 'surface_geopotential',
                       'type': 'an',
                       'cell_methods': None},
              'sftlf': {'ecmwf_name': 'lsm',
                        'ecmwf_tag': '172.128',
                        'standard_name': 'land_area_fraction',
                        'type': 'an',
                        'cell_methods': None,
                        'units': '1'}}

ecmwf_vars_forecast = {
    'pr': {'ecmwf_tag': '228.128',
           'standard_name': 'precipitation_flux',
           'type': 'fc',
           'levtype': 'sfc',
           'cell_methods': 'time: mean',
           'accumulation': True,
           'accumulation_method': 'mean',
           'scale_factor': (1000.0 / 10800.0),
           'force_positive': True,
           'units': 'kg m-2 s-1'},
    'uas': {'ecmwf_tag': '165.128',
            'standard_name': 'eastward_wind',
            'type': 'fc',
            'levtype': 'sfc',
            'least_significant_digit': 3},
    'vas': {'ecmwf_tag': '166.128',
            'standard_name': 'northward_wind',
            'type': 'fc',
            'levtype': 'sfc',
            'least_significant_digit': 3}}

ecmwf_vars_analysis = {}
