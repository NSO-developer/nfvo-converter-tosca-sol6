#!/usr/bin/env python3

import argparse
import json
import yaml
from YangToDict import YangToDict, count_empty_fields
from sol6_converter import Sol6Converter
import nso as nso
import logging
import dict_utils

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('-f', '--file', required=True, help="The TOSCA VNF")
parser.add_argument('-o', '--output', help="The output file for the convtered VNF")
parser.add_argument('-l', '--log-level',
                    choices=['DEBUG', 'INFO', 'WARNING'], default=logging.INFO, help="Log level")
parser.add_argument('-H', '--hide-output', action='store_true',
                    help="Hide the output to the console at the end")
parser.add_argument('-n', '--dry-run', action='store_true', help="Don't send VNFD to NSO")
parser.add_argument('-y', '--yang-template', required=True, help="The yang specifications file")
parser.add_argument('-g', '--no-grouping', action='store_false',
                    help="Specify if there are no grouping tags in the specifications file")

args = parser.parse_args()

logging.basicConfig(level=args.log_level)
log = logging.getLogger(__name__)

# Parse the yang specifications file into an empty dictionary
ytd = YangToDict(file=args.yang_template, log=log, g_req=args.no_grouping)
parsed_dict = ytd.parse_yang()
start_empty = count_empty_fields(parsed_dict)

# Read the tosca vnf into a dict from yaml format
with open(args.file, 'rb') as f:
    tosca_vnf = yaml.load(f.read())

# Do the actual converting to SOL006
converter = Sol6Converter(tosca_vnf, parsed_dict, log=log)
cnfv = converter.parse()

end_empty = count_empty_fields(cnfv)

print("{}% of fields filled".format(round((end_empty / start_empty)*100, 2)))

# Prune the empty fields
dict_utils.prune_empty(cnfv)

# Put the data:esti-nfv:vnf tags at the base
cnfv = {'data': {'etsi-nfv:nfv': cnfv}}

json_output = json.dumps(cnfv, indent=2)

if args.output:
    with open(args.output, 'w') as f:
        f.writelines(json_output)

if not args.hide_output:
    print(json_output)

# Store it in NSO if that's what we're doing
# This probably won't work, I haven't tested it yet
if not args.dry_run:
    converted_json = json.dumps(cnfv, indent=4, separators=(',', ': '))
    nso.store(converted_json)
