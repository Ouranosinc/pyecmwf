# The esdt_dir can be looked up at
# https://goldsmr4.gesdisc.eosdis.nasa.gov/data/

ecmwf_vars = {'phis': {'ecmwf_name': 'z',
                       'ecmwf_tag': '129.128',
                       'standard_name': 'surface_geopotential',
                       'type': 'an',
                       'cell_methods': None},
              'pr': {'ecmwf_name': 'tp',
                     'ecmwf_tag': '228.128',
                     'standard_name': 'precipitation_flux',
                     'type': 'fc',
                     'cell_methods': 'time: mean',
                     'scale_factor': 1000/(3*60*60),
                     'units': 'kg m-2 s-1'},
              'sftlf': {'ecmwf_name': 'lsm',
                        'ecmwf_tag': '172.128',
                        'standard_name': 'land_area_fraction',
                        'type': 'an',
                        'cell_methods': None,
                        'units': '1'}}
