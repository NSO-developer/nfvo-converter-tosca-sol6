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
import sys
import dict_utils
from sol6_converter import Sol6Converter
from sol6_converter_nokia import SOL6ConverterNokia
from sol6_converter_cisco import SOL6ConverterCisco
import toml

desc = "NFVO SOL6 Converter (SOLCon): Convert a SOL001 (TOSCA) YAML to SOL006 JSON"

parser = argparse.ArgumentParser(description=desc)
parser.add_argument('-f', '--file', required=True, help="The TOSCA VNF")
parser.add_argument('-o', '--output', help="The output file for the convtered VNF (JSON format), "
                                           "outputs to stdout if not specified")
parser.add_argument('-l', '--log-level',
                    choices=['DEBUG', 'INFO', 'WARNING'], default=logging.INFO, help="Log level")
# parser.add_argument('-n', '--dry-run', action='store_true', help="Don't send VNFD to NSO")
parser.add_argument('-p', '--prune', action='store_false',
                    help='Do not prune empty values from the dict')
parser.add_argument('-c', '--path-config', required=True,
                    help='Location of the paths configuration file for TOSCA')
parser.add_argument('-s', '--path-config-sol6', required=True,
                    help='Location of the paths configuration file for SOL6')

args = parser.parse_args()

log_format = "%(levelname)s - %(message)s"
logging.basicConfig(level=args.log_level, format=log_format)
log = logging.getLogger(__name__)

# Read the path configuration file
path_conf = toml.load(args.path_config)
path_conf_sol6 = toml.load(args.path_config_sol6)
path_conf = dict_utils.merge_two_dicts(path_conf, path_conf_sol6)

# Parse the yang specifications file into an empty dictionary
parsed_dict = {}

# Read the tosca vnf into a dict from yaml format
log.info("Reading TOSCA YAML file {}".format(args.file))
tosca_file = open(args.file, 'rb').read()
tosca_lines = open(args.file, 'rb').readlines()
tosca_vnf = yaml.load(tosca_file)

# Figure out what class we want to use
provider = Sol6Converter.find_provider(tosca_lines)
provider = "-".join(provider.split(" "))

# Do the actual converting to SOL006
if "cisco" in provider:
    converter = SOL6ConverterCisco(tosca_vnf, parsed_dict, variables=path_conf, log=log)
elif "nokia" in provider or "f5-networks" in provider:
    converter = SOL6ConverterNokia(tosca_vnf, parsed_dict, variables=path_conf, log=log)
else:
    raise TypeError("Unsupported provider: '{}'".format(provider))

cnfv = converter.convert()


# Prune the empty fields
if args.prune:
    cnfv = dict_utils.remove_empty_from_dict(cnfv)

# Put the data:esti-nfv:vnf tags at the base
cnfv = {'data': {'etsi-nfv:nfv': cnfv}}

json_output = json.dumps(cnfv, indent=2)


if args.output:
    with open(args.output, 'w') as f:
        f.writelines(json_output)

if not args.output:
    sys.stdout.write(json_output)
