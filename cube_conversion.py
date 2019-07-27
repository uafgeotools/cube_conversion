"""
cube_conversion.py

Authors: Alex Iezzi (amiezzi@alaska.edu),
         David Fee (dfee1@alaska.edu),
         Kathleen McKee,
         Liam Toney (ldtoney@alaska.edu)

Geophysical Institute, University of Alaska Fairbanks

This code converts the UAF infrasound group DATA-CUBE files into miniseed files
of a desired length of time with specified name. Output miniseed data are ready
for IRIS upload and have units of Pa (although maybe we shouldn't apply the
calib... future change). The current version of the code runs for all files in
a given digitizer folder. The code can differentiate between channels. The temp
directory should be empty and will be used as a work environment. Add the
gipptools-2015.225/bin (or newer) path to your bash profile before running this
code. Within gipptools, the code calls: cube2mseed, mseedcut, and mseedrename.
gipptools available currently at:

https://www.gfz-potsdam.de/en/section/geophysical-deep-sounding/infrastructure/geophysical-instrument-pool-potsdam-gipp/software/gipptools/
"""

import os
import subprocess
import glob
import obspy
import json

# ----------------
# INPUT PARAMETERS
# ----------------

# Input directory for CUBE files
INPUT_DIR = '/Users/ldtoney/Downloads/cube_data/2019-07-25_dump/CUBE3_AT7/190720'

# Temporary directory for CUBE/miniseed files
TEMP_DIR = '/Users/ldtoney/Downloads/cube_data/converted/tmp'

# Output directory for miniseed file
OUTPUT_DIR = '/Users/ldtoney/Downloads/cube_data/converted/miniseed'

# Location of digitizers.json and sensors.json
METADATA_DIR = '/Users/ldtoney/repos/cubeconversion'

# Load digitizer-sensor pairings file
with open('/Users/ldtoney/Downloads/cube_data/digitizer_sensor_pairs.json') as f:
    digitizer_sensor_pairs = json.load(f)

DIGITIZER = 'AEY'
SENSOR = digitizer_sensor_pairs[DIGITIZER]

NETWORK_CODE = 'AV'    # SEED network code (constant for each experiment)
STATION_CODE = 'GAIA'  # SEED station code (change for each digitizer-sensor combo)
CHANNEL_CODE = 'DDF'   # SEED channel code (e.g. BDF, HDF, etc.)
LOCATION_CODE = '04'   # SEED location code (if None, choose automatically)

TRACE_DUR = 'HOUR'  # 'HOUR' is standard; other valid lengths can be used for
                    # the 'mseedcut' tool - see documentation

BITWEIGHT = 2.44140625e-7  # [V/ct]

DEFAULT_SENSITIVITY = 0.009  # [V/Pa] <-- I think? Default sensor sensitivity
DEFAULT_OFFSET = -0.015      # [V] Default digitizer offset

# Reverse polarity list for 2016 Yasur deployment only!
REVERSE_POLARITY_LIST = ['YIF1', 'YIF2', 'YIF3', 'YIF4', 'YIF5', 'YIF6',
                         'YIFA', 'YIFB', 'YIFC', 'YIFD']

# ----------------------------
# PRELIMINARY CONVERSION STUFF
# ----------------------------

# Sensor sensitivities in V/Pa(?)
with open(os.path.join(METADATA_DIR, 'sensors.json')) as f:
    sensitivities = json.load(f)
try:
    sensitivity = sensitivities[SENSOR]
except KeyError:
    print(f'No matching sensitivities. Using default of {DEFAULT_SENSITIVITY} '
          f'V/Pa.')
    sensitivity = DEFAULT_SENSITIVITY

# Digitizer offsets in V
with open(os.path.join(METADATA_DIR, 'digitizers.json')) as f:
    digitizer_offsets = json.load(f)
try:
    offset = digitizer_offsets[DIGITIZER]
except KeyError:
    print(f'No matching offset values. Using default of {DEFAULT_OFFSET} V.')
    offset = DEFAULT_OFFSET

# ------------------------
# CONVERT TO MSEED FILE(S)
# ------------------------

# Convert raw files to day-long files in the temporary directory
print('Running cube2mseed on raw files...')
raw_files = glob.glob(os.path.join(INPUT_DIR, '*'))
print(f'Found {len(raw_files)} raw file(s).')
for tmp_file in raw_files:
    print(tmp_file)
    subprocess.run(['cube2mseed', '--verbose', '--resample=SINC',
                    f'--output-dir={TEMP_DIR}', tmp_file])

# Create list of all day-long files
day_file_list = glob.glob(os.path.join(TEMP_DIR, '*'))

# Cut the converted day-long files into smaller traces (e.g. hour)
subprocess.run(['mseedcut', '--verbose', f'--output-dir={TEMP_DIR}',
                f'--file-length={TRACE_DUR}', TEMP_DIR])

# Remove the day-long files from the temporary directory
for file in day_file_list:
    os.remove(file)

# Loop through each cut file and assign the channel number, editing the simple
# metadata (automatically distinguish between a 3-element array or single
# sensor)
print('Adding metadata to miniseed files...')
cut_file_list = glob.glob(os.path.join(TEMP_DIR, '*'))
for file in cut_file_list:
    st = obspy.read(file)
    tr = st[0]
    tr.stats.network = NETWORK_CODE
    tr.stats.station = STATION_CODE
    tr.stats.channel = CHANNEL_CODE
    tr.data = tr.data * BITWEIGHT    # Convert from counts to V
    tr.data = tr.data + offset       # Remove voltage offset
    tr.data = tr.data / sensitivity  # Convert from V to Pa
    if STATION_CODE in REVERSE_POLARITY_LIST:
        tr.data = tr.data * -1

    # If no location code was provided, choose one automatically
    if not LOCATION_CODE:
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
            raise ValueError('File ending not understood.')
    # Otherwise, use explicitly provided code
    else:
        location_id = LOCATION_CODE
        channel_pattern = '*.pri0'  # Or just use '*' here for all files?
    tr.stats.location = location_id

    st.write(file, format='MSEED')

    # This is the template for the seed naming scheme
    name_template = f'{NETWORK_CODE}.{STATION_CODE}.{location_id}.{CHANNEL_CODE}.%Y.%j.%H'

    # Rename cut files according to channel number; place in output directory
    subprocess.run(['mseedrename', '--verbose', f'--template={name_template}',
                    f'--include-pattern={channel_pattern}',
                    '--transfer-mode=MOVE', f'--output-dir={OUTPUT_DIR}',
                    file])

print('Done')
