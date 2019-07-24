"""
cube_conversion.py

Authors: Alex Iezzi (amiezzi@alaska.edu),
         David Fee (dfee1@alaska.edu),
         Kathleen McKee,
         Liam Toney (ldtoney@alaska.edu)

Geophysical Institute, University of Alaska Fairbanks

This code converts the UAF infrasound group DATA-CUBE files into miniseed files
of a desired length of time with specified name. Output minseed data are ready
for IRIS upload (although maybe we shouldn't apply the calib?...future change).
The current version of the code runs for all files in a given digitizer folder.
Code can differentiate between channels. The temp_directory should be empty and
will be used as a work environment. Add gipptools-2015.225/bin (or newer) path
to your bash profile before running this code. Within gipptools, the code
calls: cube2mseed, mseedcut, and mseedrename. gipptools available currently at:

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
INPUT_DIR = '/Users/ldtoney/repos/cubeconversion/F81_AF0'

# Temporary directory for CUBE/miniseed files
TEMP_DIR = '/Users/ldtoney/repos/cubeconversion/data/temp'

# Output directory for miniseed files
OUTPUT_DIR = '/Users/ldtoney/repos/cubeconversion/data/mseed'

# Location of digitizers.json and sensors.json
METADATA_DIR = '/Users/ldtoney/repos/cubeconversion'

SENSOR = 'SN51'
DIGITIZER = 'AFO'

NETWORK_CODE = 'HV'   # SEED network code (constant for each experiment)
STATION_CODE = 'F81'  # SEED station code (change for each digitizer-sensor combo)
CHANNEL_CODE = 'DDF'  # SEED-compliant channel code (e.g. BDF, HDF, etc.)

TRACE_DUR = 'HOUR'  # 'HOUR' is standard; other valid lengths can be used for
                    # the 'mseedcut' tool - see documentation

BITWEIGHT = 2.44140625e-7  # [V/ct]

DEFAULT_OFFSET = -0.015  # [V] Default digitizer offset

# Reverse polarity list for 2016 Yasur deployment only!
REVERSE_POLARITY_LIST = ['YIF1', 'YIF2', 'YIF3', 'YIF4', 'YIF5', 'YIF6',
                         'YIFA', 'YIFB', 'YIFC', 'YIFD']

# ----------------------------
# PRELIMINARY CONVERSION STUFF
# ----------------------------

# Sensor sensitivities in Pa/V(?)
with open(os.path.join(METADATA_DIR, 'sensors.json')) as f:
    sensitivities = json.load(f)
sensitivity = sensitivities[SENSOR]

# Digitizer offsets in V
with open(os.path.join(METADATA_DIR, 'digitizers.json')) as f:
    digitizer_offsets = json.load(f)
try:
    offset = digitizer_offsets[DIGITIZER]
except KeyError:
    print(f'No matching offset values. Using default of {DEFAULT_OFFSET} V.')
    offset = DEFAULT_OFFSET






#%%
#############################
### Convert to mseed file ###
#############################
# Convert the raw file to day long files into the temporary directory
print('Running cube2mseed on raw files...')
infiles= glob.glob(INPUT_DIR + "*/*")
print('Found %d files' % len(infiles))
for ftmp in infiles:
    print(ftmp)
    subprocess.call(['cube2mseed', '--verbose', '--resample=SINC', '--output-dir=' + TEMP_DIR, ftmp])
#subprocess.call(['cube2mseed', '--verbose', '--resample=SINC', '--output-dir=' + temp_directory, input_directory])

full_file_list = glob.glob(TEMP_DIR + "*")
print('Done')
# Cut the converted file into smaller traces (e.g. hour)
subprocess.call(['mseedcut', '--verbose', '--output-dir=' + TEMP_DIR, '--file-length=' + TRACE_DUR, TEMP_DIR])

# Remove the day files from the temporary directory before remaning the files
for file in full_file_list:
    os.remove(file)

# Loop through each cut file and assign the channel number
# This section will edit the simple metadata
# This part of the code can automatically distinguish between a 3 element array or single sensor
print('Adding metadata to miniseed files')
cut_file_list = glob.glob(TEMP_DIR + "*")
for file in cut_file_list:
    st = obspy.read(file)
    tr = st[0]
    tr.stats.station = STATION_CODE
    tr.stats.network = NETWORK_CODE
    tr.stats.channel = CHANNEL_CODE
    tr.data = tr.data * BITWEIGHT  # Convert from counts to V
    tr.data = tr.data + offset  # Remove voltage offset
    tr.data = tr.data / sensitivity  # Convert from V to Pa
    if STATION_CODE in REVERSE_POLARITY_LIST:
        tr.data = tr.data * -1
    if file.endswith('.pri0'):
        location_id = '01'                    # channel 1
        channel_pattern = '*.pri0'
        tr.stats.location = location_id
    elif file.endswith('.pri1'):
        location_id = '02'                    # channel 2
        channel_pattern = '*.pri1'
        tr.stats.location = location_id
    elif file.endswith('.pri2'):
        location_id = '03'                    # channel 3
        channel_pattern = '*.pri2'
        tr.stats.location = location_id
    else:
        print ('Error')
    st.write(file, format="mseed")

    # This is the template for the seed naming scheme
    name_template = NETWORK_CODE + '.' + STATION_CODE + '.' + location_id + '.' + CHANNEL_CODE + '.' + '%Y.%j.%H'

    # Rename the cut files according to the channel number and placed in output directory
    subprocess.call(['mseedrename', '--verbose', '--template=' + name_template, '--include-pattern=' + channel_pattern, '--transfer-mode=MOVE', '--output-dir=' + OUTPUT_DIR, file])
