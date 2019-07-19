###############################################################################################################
# Authors: Alex Iezzi, David Fee, Kathleen McKee
# Contact: amiezzi@alaska.edu, dfee1@alaska.edu
# Geophysical Institute: University of Alaska Fairbanks
# Created: 03-Feb-2016
# Last Revision: 12-August-2019
################################################################################################################
# This code converts the UAF infrasound group DATA-CUBE files into miniseed files of a desired length of time with specified name
# Output minseed data are ready for IRIS upload (although maybe we shouldn't apply the calib?...future change)
# The current version of the code runs for all files in a given digitizer folder
# Code can differentiate between channels
# The temp_directory should be empty and will be used as a work environment
# Add gipptools-2015.225/bin (or newer) path your bash profile before running this code
# gipptools available currently at: https://www.gfz-potsdam.de/en/section/geophysical-deep-sounding/infrastructure/geophysical-instrument-pool-potsdam-gipp/software/gipptools/
# Within gipptools, the code calls: cube2mseed, mseedcut, and mseedrename
################################################################################################################

#%%
##############################
### Import necessary modules ###
##############################
import os, subprocess
import glob
import obspy

#%%
########################
### INPUT PARAMETERS ###
########################

#AEX: SI01, SN49
#AEY: SI02, SN50
#AF0: SI03, SN51%SN48?
#AF1: SI04, SN48
#AF2: SI05, SN47
#AS0: SI06, SN73
#AT7: SI07, SN74

input_directory = '/Users/dfee/Documents/kilauea/erz2018/campaign/data/raw/F81_AF0/'  	#input directory for CUBE files
temp_directory = '/Users/dfee/Documents/kilauea/erz2018/campaign/data/temp/'			#temporary directory for CUBE/miniseed files
output_directory = '/Users/dfee/Documents/kilauea/erz2018/campaign/data/mseed/'			#output directory for miniseed files
drct='/Users/dfee/repos/cubeconversion/'	#repository directory for location of digitizer and sensor text files (just put this in module maybe?)

station_code = 'F81'				# change for each digitizer-sensor combo; 4 characters
sensor = 'SN51'

network_code = 'HV'					#seed network constant for each experiment; 2 characters
channel_code = 'DDF'				#seed-compliant channel code (e.g. BDF, high broadband (80<=samplerate<250 Hz), instrument code, infrasound); 3 characters

trace_duration = 'HOUR'        		#'HOUR' is standard, other valid lengths can be used for the 'mseedcut' tool; see documentation

#%%
#some prelminary conversion stuff
digitizer = input_directory[-4:-1]
#digitizer = 'AEX'

def get_sens_offset(drct,digitizer,sensor):
########################################################################
# Obtain the sensor sensitivity and digitizer offset automatically ###
# Each  cube-sensor configuration has unique offset voltage
########################################################################
    import numpy as np
    digitizer_data = np.genfromtxt(drct+'digitizers.txt', dtype='str')
    sensor_data = np.genfromtxt(drct+'sensors.txt', dtype='str')

    # Loop through to get digitizer offset
    UAF_digitizers = ['AEX', 'AEY','AF0', 'AF1', 'AF2', 'AF3', 'AS0', 'AT7']
    if digitizer in UAF_digitizers:
        dig_index, a = np.where(digitizer_data == digitizer)
        dig_index = int(np.asarray(dig_index))
        offset_val = float(digitizer_data[dig_index,1])
    else:
        offset_val = -0.015
        print('No matching offset values, using default!')

    # Loop through to get sensor sensitivity
    sens_index, a = np.where(sensor_data == sensor)
    sens_index = int(np.asarray(sens_index))
    sens = float(sensor_data[sens_index,1])

    return sens,offset_val

# The Yasur deployment had a polarity reversal at the Chap60 connector. 
# Therefore, this list of station names will be multiplied by -1
# The reversal was fixed prior to Summer 2017 deployments
reverse_polarity_list = ['YIF1', 'YIF2', 'YIF3', 'YIF4', 'YIF5', 'YIF6', 'YIFA', 'YIFB', 'YIFC', 'YIFD']

###################################################
### Choose either UAF or General Specifications ###
###################################################

# UAF Specifications
# Use Lines 141-143; Comment out line 140
sens,offset_val = get_sens_offset(digitizer,sensor)
sens = sens/4.5						# Because of the BoB built by Jay and Alex
bweight = 2.4064533177e-7 			# Bitweight in V/ct; given by Jay 


# General Specifications
# Use Line 140; Comment out lines 141-143
#offset_val = 0
#sens = 0.009						# Sensitivity
#bweight = 2.44140625e-7 			# Bitweight in V/ct given by Albrecht
#calib = bweight/sens


#%%
#############################
### Convert to mseed file ###
#############################
# Convert the raw file to day long files into the temporary directory
print('Running cube2mseed on raw files...')
infiles= glob.glob(input_directory + "*/*")
print('Found %d files' % len(infiles))
for ftmp in infiles:
    print(ftmp)
    subprocess.call(['cube2mseed', '--verbose', '--resample=SINC', '--output-dir=' + temp_directory, ftmp])
#subprocess.call(['cube2mseed', '--verbose', '--resample=SINC', '--output-dir=' + temp_directory, input_directory])

full_file_list = glob.glob(temp_directory + "*")
print('Done')
# Cut the converted file into smaller traces (e.g. hour)
subprocess.call(['mseedcut', '--verbose', '--output-dir=' + temp_directory, '--file-length=' + trace_duration, temp_directory])

# Remove the day files from the temporary directory before remaning the files
for file in full_file_list:
	os.remove(file)

# Loop through each cut file and assign the channel number
# This section will edit the simple metadata
# This part of the code can automatically distinguish between a 3 element array or single sensor
print('Adding metadata to miniseed files')
cut_file_list = glob.glob(temp_directory + "*")
for file in cut_file_list:
	st = obspy.read(file)
	tr = st[0]
	tr.stats.station = station_code
	tr.stats.network = network_code
	tr.stats.channel = channel_code
	#tr.data = tr.data * calib			# Use for general specifications
	tr.data = tr.data * bweight 		# Use for UAF specifications
	tr.data = tr.data + offset_val      # Use for UAF specifications; remove voltage offset
	tr.data = tr.data / sens 			# Use for UAF specifications
	if station_code in reverse_polarity_list:
		tr.data = tr.data * -1
	if file.endswith('.pri0'):
		location_id = '01'					# channel 1
		channel_pattern = '*.pri0'
		tr.stats.location = location_id
	elif file.endswith('.pri1'):
		location_id = '02'					# channel 2
		channel_pattern = '*.pri1'
		tr.stats.location = location_id
	elif file.endswith('.pri2'):
		location_id = '03'					# channel 3
		channel_pattern = '*.pri2'
		tr.stats.location = location_id
	else:
		print ('Error')
	st.write(file, format="mseed")

	# This is the template for the seed naming scheme
	name_template = network_code + '.' + station_code + '.' + location_id + '.' + channel_code + '.' + '%Y.%j.%H'

	# Rename the cut files according to the channel number and placed in output directory
	subprocess.call(['mseedrename', '--verbose', '--template=' + name_template, '--include-pattern=' + channel_pattern, '--transfer-mode=MOVE', '--output-dir=' + output_directory, file])
