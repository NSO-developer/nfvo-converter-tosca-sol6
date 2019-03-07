#!/usr/bin/env python3
"""

"""
__author__ = "Aaron Steeleso"
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

supported_providers = {
    "cisco": SOL6ConverterCisco,
    "nokia": SOL6ConverterNokia
}

parser = argparse.ArgumentParser(description=desc)
parser.add_argument('-f', '--file', required=True, help="The TOSCA VNF YAML file to be processed")
parser.add_argument('-o', '--output', help="The output file for the convtered VNF (JSON format), "
                                           "outputs to stdout if not specified")
parser.add_argument('-l', '--log-level',
                    choices=['DEBUG', 'INFO', 'WARNING'], default=logging.INFO,
                    help="Set the log level for standalone logging")
# parser.add_argument('-n', '--dry-run', action='store_true', help="Don't send VNFD to NSO")
parser.add_argument('-p', '--prune', action='store_false',
                    help='Do not prune empty values from the dict')
parser.add_argument('-c', '--path-config', required=True,
                    help='Location of the paths configuration file for TOSCA paths (TOML format)')
parser.add_argument('-s', '--path-config-sol6', required=True,
                    help='Location of the paths configuration file for SOL6 paths (TOML format)')
parser.add_argument('-r', '--provider',
                    help='Specifically provide the provider instead of trying to read it from the '
                         'file. Supported providers: {}'.format(list(supported_providers.keys())))

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
# If it was specifically provided as a parameter
if args.provider:
    provider = args.provider
else:
    # Try to figure out what it is
    provider = Sol6Converter.find_provider(tosca_lines)
    provider = "-".join(provider.split(" "))

# Initialize the proper converter object for the given provider
if provider.lower() not in supported_providers:
    for s_p in supported_providers:
        if s_p in provider.lower():
            provider = s_p
            
if provider.lower() in supported_providers:
    log.info("Starting conversion with provider '{}'".format(provider))
    converter = supported_providers[provider](tosca_vnf, parsed_dict, variables=path_conf, log=log)
else:
    raise TypeError("Unsupported provider: '{}'".format(provider))
# Do the actual converting logic
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
