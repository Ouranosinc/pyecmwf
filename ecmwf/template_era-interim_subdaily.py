import ecmwf

dataset = 'era-interim' # from ecmwf_datasets.py
var_name = 'uas' # from ecwmf_variables.py
experiment = 'fc'
title = 'ERA-Interim'
source = 'Reanalysis'
path_output = '/path/to/output'
initial_year = 1979
final_year = 2016

ecmwf.download_and_convert_by_year(
    dataset, var_name, path_output, initial_year, final_year, title, source,
    experiment)
