#!/usr/bin/env python3
"""

"""
__author__ = "Aaron Steele, Niraj Chandak"
__credits__ = ["Frederick Jansson"]
__version__ = "0.0.1"

import argparse
import json
import yaml
import logging
import dict_utils
import nso as nso
from sol6_converter import Sol6Converter
import toml

desc = "NFVO SOL6 Converter (SOLCon): Convert a SOL001 (TOSCA) YAML to SOL006 JSON"

parser = argparse.ArgumentParser(description=desc)
parser.add_argument('-f', '--file', required=True, help="The TOSCA VNF")
parser.add_argument('-o', '--output', help="The output file for the convtered VNF (JSON format)")
parser.add_argument('-l', '--log-level',
                    choices=['DEBUG', 'INFO', 'WARNING'], default=logging.INFO, help="Log level")
parser.add_argument('-H', '--hide-output', action='store_true',
                    help="Do not show output in the console at the end of conversion")
# parser.add_argument('-n', '--dry-run', action='store_true', help="Don't send VNFD to NSO")
# parser.add_argument('-y', '--yang-template', help="The yang specifications file")
# parser.add_argument('-g', '--no-grouping', action='store_false',
#                    help="Specify if there are no grouping tags in the specifications file")
parser.add_argument('-p', '--prune', action='store_true', help='Prune empty values from the dict')
parser.add_argument('-c', '--path-config', required=True, help='Location of the paths configuration file')

args = parser.parse_args()

log_format = "%(levelname)s - %(message)s"
logging.basicConfig(level=args.log_level, format=log_format)
log = logging.getLogger(__name__)

# Read the path configuration file
path_conf = toml.load(args.path_config)

# Parse the yang specifications file into an empty dictionary
parsed_dict = {}

# Read the tosca vnf into a dict from yaml format
log.info("Reading TOSCA YAML file {}".format(args.file))
with open(args.file, 'rb') as f:
    tosca_vnf = yaml.load(f.read())

# Do the actual converting to SOL006
converter = Sol6Converter(tosca_vnf, parsed_dict, variables=path_conf, log=log)
cnfv = converter.parse()


# Prune the empty fields
if args.prune:
    cnfv = dict_utils.remove_empty_from_dict(cnfv)

# Put the data:esti-nfv:vnf tags at the base
cnfv = {'data': {'etsi-nfv:nfv': cnfv}}

json_output = json.dumps(cnfv, indent=2)


if args.output:
    with open(args.output, 'w') as f:
        f.writelines(json_output)

if not args.hide_output:
    log.info(json_output)

# Always do dry run for now
args.dry_run = True
# Store it in NSO if that's what we're doing
# This probably won't work, I haven't tested it yet
if not args.dry_run:
    converted_json = json.dumps(cnfv, indent=4, separators=(',', ': '))
    nso.store(converted_json)
