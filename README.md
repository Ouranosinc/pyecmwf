# pyecmwf

## Setup

This is based on the documentation at:
https://software.ecmwf.int/wiki/display/WEBAPI/Access+ECMWF+Public+Datasets

Step 1: Copy the key (see documentation) to $HOME/.ecmwfapirc

Step 2: Download client, then for local install:
export PYTHONPATH=/home/username/lib/python2.7/site-packages
python setup.py install --prefix=/home/username

## Usage

Examples are found in the template files.

To identify the variables parameter tag, go to the ecmwf web interface,
http://apps.ecmwf.int/datasets/, select the variable, click on
"View the MARS request" and lookup the "param" value. This is also where
variables that are available as analysis and/or forecast can be identified.
Forecast have "step": "3/6/9/12" & "time": "00:00:00/12:00:00" & "type": "fc".
Analysis have "step": "0" & "time": "00:00:00/06:00:00/12:00:00/18:00:00" &
"type": "an".

## Limitations

- Only tested with ERA-Interim.
