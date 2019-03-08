#!/usr/bin/env python3
"""

"""
__author__ = "Aaron Steele"
__credits__ = ["Frederick Jansson"]
__version__ = "0.2.0"

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


class SolCon:
    def __init__(self):
        self.log = None
        self.variables = None
        self.tosca_lines = None
        self.tosca_vnf = None
        self.converter = None
        self.provider = None
        self.supported_providers = None

        self.desc = "NFVO SOL6 Converter (SolCon): Convert a SOL001 (TOSCA) YAML to SOL006 JSON"

        self.supported_providers = {
            "cisco": SOL6ConverterCisco,
            "nokia": SOL6ConverterNokia
        }

        parser = argparse.ArgumentParser(description=self.desc)
        parser.add_argument('-f', '--file',
                            help="The TOSCA VNF YAML file to be processed")
        parser.add_argument('-o', '--output',
                            help="The output file for the convtered VNF (JSON format), "
                                 "outputs to stdout if not specified")
        parser.add_argument('-l', '--log-level',
                            choices=['DEBUG', 'INFO', 'WARNING'], default=logging.INFO,
                            help="Set the log level for standalone logging")
        # parser.add_argument('-n', '--dry-run', action='store_true', help="Don't send VNFD to NSO")
        parser.add_argument('-p', '--prune', action='store_false',
                            help='Do not prune empty values from the dict')
        parser.add_argument('-c', '--path-config',
                            help='Location of the paths configuration file for TOSCA paths '
                                 '(TOML format)')
        parser.add_argument('-s', '--path-config-sol6',
                            help='Location of the paths configuration file for SOL6 paths '
                                 '(TOML format)')
        parser.add_argument('-r', '--provider',
                            help='Specifically provide the provider instead of trying to read '
                                 'it from the file. Supported providers: {}'
                            .format(list(self.supported_providers.keys())))
        parser.add_argument('-i', '--interactive', action='store_true',
                            help='Initiate the interactive mode for the program')

        args = parser.parse_args()
        self.args = args
        self.parser = parser

        if args.interactive:
            self.interactive_mode()
            return

        if not args.file or not args.path_config or not args.path_config_sol6:
            print("error: the following arguments are required: -f/--file, -c/--path-config, "
                  "-s/--path-config-sol6")

        # Initiate logging
        self.log = self.start_logging(args.log_level)

        # Read the configs
        self.variables = self.read_configs(args.path_config, args.path_config_sol6)

        # Parse the yang specifications file into an empty dictionary
        self.parsed_dict = {}

        # Read the data from the provided yaml file into variables
        self.tosca_vnf, self.tosca_lines = self.read_tosca_yaml(args.file)

        # Determine what provider to use
        self.provider = self.find_provider(args.provider, self.tosca_lines).lower()

        # Initialize the proper converter object for the given provider
        self.converter = self.initialize_converter(self.provider, self.supported_providers)

        # Do the actual converting logic
        cnfv = self.converter.convert(provider=self.provider)

        self.output(cnfv)

    @staticmethod
    def start_logging(log_level):
            log_format = "%(levelname)s - %(message)s"
            logging.basicConfig(level=log_level, format=log_format)
            return logging.getLogger(__name__)

    @staticmethod
    def read_configs(tosca_config, sol6_config):
        # Read the path configuration file
        variables = toml.load(tosca_config)
        variables_sol6 = toml.load(sol6_config)
        return dict_utils.merge_two_dicts(variables, variables_sol6)

    def output(self, cnfv):
        # Prune the empty fields
        if self.args.prune:
            cnfv = dict_utils.remove_empty_from_dict(cnfv)
        # Put the data:esti-nfv:vnf tags at the base
        cnfv = {'data': {'etsi-nfv:nfv': cnfv}}

        json_output = json.dumps(cnfv, indent=2)

        if self.args.output:
            with open(self.args.output, 'w') as f:
                f.writelines(json_output)

        if not self.args.output:
            sys.stdout.write(json_output)

    def read_tosca_yaml(self, file):
        # Read the tosca vnf into a dict from yaml format
        self.log.info("Reading TOSCA YAML file {}".format(file))
        file_read = open(file, 'rb').read()
        file_lines = open(file, 'rb').readlines()
        parsed_yaml = yaml.load(file_read)
        return parsed_yaml, file_lines

    def initialize_converter(self, sel_provider, valid_providers):
        # If the provider is not a part of a valid provider, i.e. 'cisco' in ['cisco', 'nokia'],
        # check if any of the valid providers are in the sel_provider,
        #   i.e. 'cisco' in '&provider-cisco'
        if sel_provider not in valid_providers:
            found = False
            for s_p in valid_providers:
                if s_p in sel_provider:
                    sel_provider = s_p
                    self.provider = s_p
                    found = True
            if not found:
                raise TypeError("Unsupported provider: '{}'".format(sel_provider))
        # We found a proper provider, so we can start doing things
        self.log.info("Starting conversion with provider '{}'".format(sel_provider))
        return valid_providers[sel_provider](self.tosca_vnf, self.parsed_dict,
                                             variables=self.variables, log=self.log)

    @staticmethod
    def find_provider(arg_provider, file_lines):
        # Figure out what class we want to use
        # If it was specifically provided as a parameter
        if arg_provider:
            return arg_provider
        else:
            # Try to figure out what it is
            return "-".join(Sol6Converter.find_provider(file_lines).split(" "))

    def interactive_mode(self):
        print("Interactive Mode Started")
        args = self.args

        if args.log_level:
            # Initiate logging
            self.log = self.start_logging(args.log_level)

            print("Log level set to {}. (y/n)?".format(args.log_level))
        else:
            print("Select log level:")
            print(self.parser)

        return
        # Read the configs
        self.variables = self.read_configs(args.path_config, args.path_config_sol6)

        # Parse the yang specifications file into an empty dictionary
        self.parsed_dict = {}

        # Read the data from the provided yaml file into variables
        self.tosca_vnf, self.tosca_lines = self.read_tosca_yaml(args.file)

        # Determine what provider to use
        self.provider = self.find_provider(args.provider, self.tosca_lines).lower()

        # Initialize the proper converter object for the given provider
        self.converter = self.initialize_converter(self.provider, self.supported_providers)

        # Do the actual converting logic
        cnfv = self.converter.convert(provider=self.provider)

        self.output(cnfv)


def main():
    SolCon()


if __name__ == '__main__':
    main()
