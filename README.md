cube_conversion
===============

These command-line tools convert [DiGOS](https://digos.eu/) DATA-CUBE³ files into
miniSEED files of a desired length of time with specified metadata, and produce
validated StationXML files containing deployment, sensor, and digitizer information
including sensor responses adjusted for individual sensor sensitivities. Output miniSEED
files have units of Pa, unless the user selects to export the files in a form suitable
for submission to EarthScope (formerly IRIS) — namely, integer counts. The miniSEED
conversion tool can differentiate between channels for 3 channel DATA-CUBE³ files and
optionally extract coordinates from the digitizer's GPS. The code only looks for files
from digitizers defined in the `digitizer_sensor_pairs.json` file. Therefore, this file
must be updated if pairings change or new pairings are added. The user can specify a
custom "breakout box factor" for setups that modify the signal voltage via a voltage
divider. This tool is currently only set up for conversion of infrasound data, but
future updates could accommodate seismic as well.

Installation
------------

It's recommended that you run this script within a new or pre-existing
[conda](https://docs.conda.io/projects/conda/en/stable/) environment.
(If you choose the latter option, ensure that your environment contains all of
the packages listed in the [Dependencies](#dependencies) section.)

To create a new conda environment for use with this and other _uafgeotools_
packages, execute the following terminal command:
```
conda create -n uafinfra -c conda-forge obspy
```
This creates a new environment called `uafinfra` with ObsPy and its dependencies
installed.

You must also install GIPPtools and add it to your path as described in the
[Dependencies](#dependencies) section.

To install _cube_conversion_, simply execute the following terminal commands with your
target conda environment activated:
```
git clone https://github.com/uafgeotools/cube_conversion.git
cd cube_conversion
pip install -e .
```

Dependencies
------------

Python packages:

* [ObsPy](http://docs.obspy.org/)

...and its dependencies, which you don't really have to be concerned about if
you're using conda!

You also need to install
[GIPPtools](https://www.gfz-potsdam.de/en/section/geophysical-imaging/infrastructure/geophysical-instrument-pool-potsdam-gipp/software/gipptools/)
and add it to your `PATH`.

* Version 2024.354 or newer is required and we encourage the user to always use the latest version.

* Add GIPPtools to your `PATH` by adding the following line to your
  `~/.zshrc` (for Z shell), `~/.bash_profile`, or `~/.bashrc` (for Bash) :
  ```
  export PATH=$PATH:/path/to/gipptools-????.???/bin
  ```
  Replace `????.???` with your version of GIPPtools — e.g. `2024.170` — and
  ensure you've provided the right path.

Supplemental files
------------------

* `digitizer_sensor_pairs.json` — UAF digitizer-sensor pairs (**EDIT ME!**)

* `digitizer_offsets.json` — Digitizer offsets in V (We have found that each
                             digitizer has a slight voltage offset from zero)

* `sensor_sensitivities.json` — Infrasound sensor model, sensitivity in V/Pa,
  and frequency of sensitivity measurement in Hz

Usage
-----

To run either command-line tool first activate your conda environment, e.g.,
```
conda activate uafinfra  # Or your pre-existing env
```

## `cube_convert`

To print the conversion script's help menu, run:
```
cube_convert --help  # Or: python /path/to/cube_conversion/cube_convert.py --help
```
The help menu is shown below.
```
usage: cube_convert [-h] [-v] [--grab-gps] [--bob-factor BREAKOUT_BOX_FACTOR]
                    [--earthscope]
                    input_dir [input_dir ...] output_dir network station
                    {01,02,03,04,AUTO} {AUTO,BDF,HDF,CDF}

Convert DATA-CUBE files to miniSEED files while trimming, adding metadata, and renaming.
Optionally extract coordinates from digitizer GPS.

positional arguments:
  input_dir             one or more directories containing raw DATA-CUBE files (all files
                        must originate from a single digitizer) [wildcards (*) supported]
  output_dir            directory for output miniSEED and GPS-related files
  network               desired SEED network code (2 characters, A-Z)
  station               desired SEED station code (3-5 characters, A-Z & 0-9)
  {01,02,03,04,AUTO}    desired SEED location code (if AUTO, choose automatically for 3
                        channel DATA-CUBE files)
  {AUTO,BDF,HDF,CDF}    desired SEED channel code (if AUTO, determine automatically using
                        SEED convention [preferred])

options:
  -h, --help            show this help message and exit
  -v, --verbose         enable verbosity for GIPPtools commands
  --grab-gps            additionally extract coordinates from digitizer GPS
  --bob-factor BREAKOUT_BOX_FACTOR
                        factor by which to divide sensitivity values (for custom breakout
                        boxes [4.5 for UAF DATA-CUBEs])
  --earthscope          format miniSEED files for EarthScope (formerly IRIS) data upload
```
For example, the command
```
cube_convert ~/data/raw/*/ ~/data/mseed/ AV GAIA 01 AUTO --grab-gps --bob-factor 4.5
```
means "convert all files in the subdirectories of `~/data/raw/` and place in
`~/data/mseed/` with network code **AV**, station code **GAIA**, location code
**01**, and an automatically determined channel code, dividing the sensitivity
by 4.5 and extracting coordinates from the digitizer's GPS."

## `cube_stationxml`

To print the StationXML generation script's help menu, run:
```
cube_stationxml --help  # Or: python /path/to/cube_conversion/cube_stationxml.py --help
```
The help menu is shown below.
```
usage: cube_stationxml [-h] [--nrl-path NRL_PATH] [--validate]
                       input_dir station_mapping [station_mapping ...] output_filename

Generate StationXML files from DATA-CUBE³ miniSEED files and metadata.

positional arguments:
  input_dir            directory containing miniSEED files and coordinate files produced
                       by cube_convert
  station_mapping      one or more mappings of the form
                       STATION_CODE:CUBE_NAME:SENSOR_SERIAL, for example UAF1:AVJ:903V2
  output_filename      filename for the output StationXML file (full path)

options:
  -h, --help           show this help message and exit
  --nrl-path NRL_PATH  path to local copy of the NRL (if not provided, uses online NRL)
  --validate           run the IRIS StationXML validator on the output file
```
For example, the command
```
cube_stationxml ~/data/miniseed/ UAF1:B52:903V2 ~/data/station.xml --validate
```
means "process all miniSEED files in `~/data/miniseed/` assuming that station **UAF1**
consisted of DATA-CUBE³ **B52** connected to sensor serial number **903V2**, and output
a StationXML file to `~/data/station.xml`, validating the output file with the IRIS
StationXML validator."

A note on SEED band codes
-------------------------

Appendix A of the
[SEED manual (version 2.4)](http://www.fdsn.org/pdf/SEEDManual_V2.4.pdf)
specifies the following guidance for band codes. Band codes are the first
letter of the channel code; e.g., the "B" in "BDF".

| Band code | Band type              | Sample rate (Hz)    | Corner period (s) |
| :-------- | :--------------------- | :------------------ | :---------------- |
| F         |                        | ≥ 1000 to < 5000    | ≥ 10              |
| G         |                        | ≥ 1000 to < 5000    | < 10              |
| D         |                        | ≥ 250 to < 1000     | < 10              |
| **C**     |                        | **≥ 250 to < 1000** | **≥ 10**          |
| E         | Extremely short-period | ≥ 80 to < 250       | < 10              |
| S         | Short-period           | ≥ 10 to < 80        | < 10              |
| **H**     | **High broadband**     | **≥ 80 to < 250**   | **≥ 10**          |
| **B**     | **Broadband**          | **≥ 10 to < 80**    | **≥ 10**          |
| M         | Mid-period             | > 1 to < 10         |                   |
| L         | Long-period            | ≈ 1                 |                   |
| V         | Very long-period       | ≈ 0.1               |                   |
| U         | Ultra long-period      | ≈ 0.01              |                   |
| R         | Extremely long-period  | ≥ 0.0001 to < 0.001 |                   |

Note that the band code depends on both the sample rate of the digitizer and
the corner period of the sensor. In `cube_convert` we allow for "B", "H", or
"C", which covers a range of sample rates from 10 to 1000 Hz, all for corner
periods of 10 s or greater. While this covers most infrasound sensors, please
confirm that your digitizer sample rate and sensor corner period fit into the
above framework.

Authors
-------

(_Alphabetical order by last name._)

David Fee  
Julia Gestrich  
Alex Iezzi  
Kathleen McKee  
Liam Toney
