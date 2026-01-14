#!/usr/bin/env python

import argparse
import os

# -----------------------------------------------------------------------------
# Advanced configuration options
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------


# Define callable main function to work with [project.scripts]
def main():

    # Set up command-line interface
    parser = argparse.ArgumentParser(
        description='Generate StationXML files from DATA-CUBE³ miniSEED files and metadata.',
        allow_abbrev=False,
    )
    parser.add_argument(
        'input_dir',
        help='directory containing miniSEED files and coordinate files produced by cube_convert',
    )
    input_args = parser.parse_args()

    # Check if input directory/ies is/are valid
    for input_dir in input_args.input_dir:
        if not os.path.exists(input_dir):
            raise NotADirectoryError(
                f'Input directory \'{input_dir}\' doesn\'t ' 'exist.'
            )


# Run the main function if this is called as a script
if __name__ == '__main__':
    main()
