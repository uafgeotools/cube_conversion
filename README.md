cube_conversion
===============

This command-line tool converts DATA-CUBE<sup>3</sup> files into miniSEED files
of a desired length of time with specified metadata. Output miniSEED files are
ready for IRIS upload and have units of Pa. The tool can differentiate between
channels for 3 channel DATA-CUBE<sup>3</sup> files and optionally extract
coordinates from the digitizer's GPS. The code only looks for files from
digitizers defined in the `digitizer_sensor_pairs.json` file. Therefore, this
file must be updated if pairings change or new pairings are added. The user can
specify a custom "breakout box factor" for setups that modify the signal voltage
via a voltage divider.

Dependencies
------------

* [Python](https://www.python.org/) >= 3.2
* [ObsPy](http://docs.obspy.org/)

...and their dependencies, which you don't really have to be concerned about if
you're using [conda](https://docs.conda.io/projects/conda/en/latest/index.html)!

It's recommended that you create a new conda environment to use with this
repository:
```
conda create -n cube_conversion -c conda-forge obspy "python>=3.2"
```

You also need to install
[GIPPtools](https://www.gfz-potsdam.de/en/section/geophysical-deep-sounding/infrastructure/geophysical-instrument-pool-potsdam-gipp/software/gipptools/)
and add it to your `PATH`.

* Version 2015.225 or newer is required.

* Add GIPPtools to your `PATH` by adding the following line to your
  `~/.bash_profile` or `~/.bashrc`:
  ```
  export PATH=$PATH:/path/to/gipptools-****.***/bin
  ```

Supplemental files
------------------

* `digitizer_sensor_pairs.json` — UAF digitizer-sensor pairs (**EDIT ME!**)

* `digitizer_offsets.json` — Digitizer offsets in V

* `sensor_sensitivities.json` — Sensor sensitivities in V/Pa

Usage
-----

To use _cube_conversion_, clone or download this repository, and then run the
following commands in a terminal window:
```
$ conda activate cube_conversion
$ python /path/to/cube_convert.py --help
```
You'll see the following help menu:
```
usage: cube_convert.py [-h] [-v] [--grab-gps]
                       [--bob-factor BREAKOUT_BOX_FACTOR]
                       input_dir output_dir network station {01,02,03,04,AUTO}
                       {AUTO,BDF,HDF,DDF}

Convert DATA-CUBE files to miniSEED files while trimming, adding metadata, and
renaming. Optionally extract coordinates from digitizer GPS.

positional arguments:
  input_dir             directory containing raw DATA-CUBE files (all files
                        must originate from a single digitizer)
  output_dir            directory for output miniSEED and GPS-related files
  network               desired SEED network code (2 characters, A-Z)
  station               desired SEED station code (3-4 characters, A-Z & 0-9)
  {01,02,03,04,AUTO}    desired SEED location code (if AUTO, choose
                        automatically for 3 channel DATA-CUBE files)
  {AUTO,BDF,HDF,DDF}    desired SEED channel code (if AUTO, determine
                        automatically using SEED convention [preferred])

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         enable verbosity for GIPPtools commands
  --grab-gps            additionally extract coordinates from digitizer GPS
  --bob-factor BREAKOUT_BOX_FACTOR
                        factor by which to divide sensitivity values (for
                        custom breakout boxes)
```

Authors
-------

(_Alphabetical order by last name._)

David Fee  
Alex Iezzi  
Kathleen McKee  
Liam Toney
