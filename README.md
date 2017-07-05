# pyecmwf

## Usage

This is based on the documentation at:
https://software.ecmwf.int/wiki/display/WEBAPI/Access+ECMWF+Public+Datasets

Step 1: Copy the key (see documentation) to $HOME/.ecmwfapirc

Step 2: Download client, then for local install:
export PYTHONPATH=/home/username/lib/python2.7/site-packages
python setup.py install --prefix=/home/username

To identify the variables parameter tag, go to the ecmwf web interface,
select the variable, click on "View the MARS request" and lookup the "param"
value.
