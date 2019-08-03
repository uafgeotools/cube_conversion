"""
cube_convert.py

Authors: Alex Iezzi (amiezzi@alaska.edu),
         David Fee (dfee1@alaska.edu),
         Kathleen McKee,
         Liam Toney (ldtoney@alaska.edu)

Geophysical Institute, University of Alaska Fairbanks

This command-line tool converts DATA-CUBE files into miniSEED files of a
desired length of time with specified metadata. Output miniSEED files are ready
for IRIS upload and have units of Pa (although maybe we shouldn't apply the
calib... future change). The tool can differentiate between channels.

Requirements:
    * GIPPtools-2015.225 or newer (add gipptools-****.***/bin to your PATH)
      https://www.gfz-potsdam.de/en/section/geophysical-deep-sounding/infrastructure/geophysical-instrument-pool-potsdam-gipp/software/gipptools/
    * Python 3.2 or newer
    * ObsPy

Usage:
    Type the following on the command line:
        $ conda activate my_env_with_obspy
        $ python cube_convert.py --help
"""

import os
import subprocess
import glob
import obspy
import json
import argparse
import numpy as np
import warnings

# warnings.filterwarnings(action='ignore', message='The encoding')
# warnings.filterwarnings(action='ignore', message='Record contains')

# -----------------------------------------------------------------------------
# Advanced configuration options
# -----------------------------------------------------------------------------
TRACE_DUR = 'HOUR'  # 'HOUR' is standard; other valid lengths can be used for
                    # the 'mseedcut' tool - see documentation

BITWEIGHT = 2.44140625e-7  # [V/ct]

DEFAULT_SENSITIVITY = 0.009  # [V/Pa] Default sensor sensitivity
DEFAULT_OFFSET = -0.015      # [V] Default digitizer offset

# Reverse polarity list for 2016 Yasur deployment
REVERSE_POLARITY_LIST = ['YIF1', 'YIF2', 'YIF3', 'YIF4', 'YIF5', 'YIF6',
                         'YIFA', 'YIFB', 'YIFC', 'YIFD']
# -----------------------------------------------------------------------------

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Convert DATA-CUBE files to miniSEED while trimming and renaming.')
parser.add_argument('input_dir', type=str,
                    help='input directory for DATA-CUBE files')
parser.add_argument('output_dir', type=str,
                    help='output directory for miniSEED files')
parser.add_argument('network', type=str,
                    help='SEED network code')
parser.add_argument('station', type=str,
                    help='SEED station code')
parser.add_argument('location', type=str,
                    help='SEED location code (if AUTO, choose automatically)')
parser.add_argument('channel', type=str,
                    help='SEED channel code (e.g. BDF, HDF, etc.)')
parser.add_argument('-v', '--verbose', action='store_true',
                    help='enable verbosity for GIPPtools commands')
input_args = parser.parse_args()

# Create temporary processing directory in the output directory
tmp_dir = os.path.join(input_args.output_dir, 'tmp')
if not os.path.exists(tmp_dir):
    os.makedirs(tmp_dir)

# Find directory containing this script
script_dir = os.path.dirname(__file__)

# Load digitizer-sensor pairings file
with open(os.path.join(script_dir, 'digitizer_sensor_pairs.json')) as f:
    digitizer_sensor_pairs = json.load(f)

# Load sensor sensitivities in V/Pa(?)
with open(os.path.join(script_dir, 'sensor_sensitivities.json')) as f:
    sensitivities = json.load(f)

# Load digitizer offsets in V
with open(os.path.join(script_dir, 'digitizer_offsets.json')) as f:
    digitizer_offsets = json.load(f)

print('----------------------------------------------------------------------')
print('Beginning conversion process...')
print('----------------------------------------------------------------------')

print(f'Network code: {input_args.network}')
print(f'Station code: {input_args.station}')
if input_args.location == 'AUTO':
    loc = 'Automatic'
else:
    loc = input_args.location
print(f'Location code: {loc}')
print(f'Channel code: {input_args.channel}')

# Gather info on files in the input dir
raw_files = glob.glob(os.path.join(input_args.input_dir, '*'))
extensions = np.unique([f.split('.')[-1] for f in raw_files]).tolist()
if len(extensions) is not 1:
    raise ValueError(f'Files from multiple digitizers found: {extensions}')

digitizer = extensions[0]
sensor = digitizer_sensor_pairs[digitizer]

# Get digitizer offset
try:
    offset = digitizer_offsets[digitizer]
except KeyError:
    warnings.warn('No matching offset values. Using default of '
                  f'{DEFAULT_OFFSET} V.')
    offset = DEFAULT_OFFSET

# Get sensor sensitivity
try:
    sensitivity = sensitivities[sensor]
except KeyError:
    warnings.warn('No matching sensitivities. Using default of '
                  f'{DEFAULT_SENSITIVITY} V/Pa.')
    sensitivity = DEFAULT_SENSITIVITY

print(f'Digitizer: {digitizer} (offset = {offset} V)')
print(f'Sensor: {sensor} (sensitivity = {sensitivity} V/Pa)')

print('----------------------------------------------------------------------')
print(f'Running cube2mseed on {len(raw_files)} raw file(s)...')
print('----------------------------------------------------------------------')
for tmp_file in raw_files:
    print(os.path.basename(tmp_file))
    args = ['cube2mseed', '--resample=SINC', f'--output-dir={tmp_dir}',
            tmp_file]
    if input_args.verbose:
        args.append('--verbose')
    subprocess.call(args)

# Create list of all day-long files
day_file_list = glob.glob(os.path.join(tmp_dir, '*'))

# Cut the converted day-long files into smaller traces (e.g. hour)
print('----------------------------------------------------------------------')
print('Running mseedcut on converted miniSEED files...')
print('----------------------------------------------------------------------')
args = ['mseedcut', f'--output-dir={tmp_dir}', f'--file-length={TRACE_DUR}',
        tmp_dir]
if input_args.verbose:
    args.append('--verbose')
subprocess.call(args)

# Remove the day-long files from the temporary directory
for file in day_file_list:
    os.remove(file)

# Loop through each cut file and assign the channel number, editing the simple
# metadata (automatically distinguish between a 3-element array or single
# sensor)
cut_file_list = glob.glob(os.path.join(tmp_dir, '*'))
print('----------------------------------------------------------------------')
print(f'Adding metadata to {len(cut_file_list)} miniSEED file(s)...')
print('----------------------------------------------------------------------')
for file in cut_file_list:
    print(os.path.basename(file))
    st = obspy.read(file)
    tr = st[0]
    tr.stats.network = input_args.network
    tr.stats.station = input_args.station
    tr.stats.channel = input_args.channel
    tr.data = tr.data * BITWEIGHT    # Convert from counts to V
    tr.data = tr.data + offset       # Remove voltage offset
    tr.data = tr.data / sensitivity  # Convert from V to Pa
    if input_args.station in REVERSE_POLARITY_LIST:
        tr.data = tr.data * -1

    # If no location code was provided, choose one automatically
    if input_args.location == 'AUTO':
        if file.endswith('.pri0'):    # Channel 1
            location_id = '01'
            channel_pattern = '*.pri0'
        elif file.endswith('.pri1'):  # Channel 2
            location_id = '02'
            channel_pattern = '*.pri1'
        elif file.endswith('.pri2'):  # Channel 3
            location_id = '03'
            channel_pattern = '*.pri2'
        else:
            raise ValueError('File ending \'.{}\' not understood.'.format(file.split('.')[-1]))
    # Otherwise, use explicitly provided code
    else:
        location_id = input_args.location
        channel_pattern = '*'  # Use all files

    tr.stats.location = location_id

    st.write(file, format='MSEED')

    # Define template for miniSEED renaming
    name_template = f'{input_args.network}.{input_args.station}.{location_id}.{input_args.channel}.%Y.%j.%H'

    # Rename cut files and place in output directory
    args = ['mseedrename', f'--template={name_template}',
            f'--include-pattern={channel_pattern}', '--transfer-mode=MOVE',
            f'--output-dir={input_args.output_dir}', file]
    if input_args.verbose:
        args.append('--verbose')
    subprocess.call(args)

print('----------------------------------------------------------------------')
print('...finished conversion process.')
print('----------------------------------------------------------------------')
