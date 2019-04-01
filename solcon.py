#!/usr/bin/env python3
"""

"""
__author__ = "Aaron Steele"
__credits__ = ["Frederick Jansson"]
__version__ = "0.5"

import argparse
import json
import yaml
import logging
import sys
import os.path
import dict_utils
from sol6_converter import Sol6Converter
from sol6_converter_nokia import SOL6ConverterNokia
from sol6_converter_cisco import SOL6ConverterCisco
import toml
log = logging.getLogger(__name__)


class SolCon:
    def __init__(self):
        self.variables = None
        self.tosca_lines = None
        self.tosca_vnf = None
        self.converter = None
        self.provider = None
        self.supported_providers = None

        print("Starting SolCon (v{})...".format(__version__))

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
        # Advanced arguments:
        parser.add_argument('-p', '--prune', action='store_false',
                            help='Do not prune empty values from the dict')
        parser.add_argument('-i', '--interactive', action='store_true',
                            help=argparse.SUPPRESS)

        args = parser.parse_args()
        self.args = args
        self.parser = parser

        if args.interactive:
            self.interactive_mode()
            return

        if not args.file or not args.path_config or not args.path_config_sol6:
            print("error: the following arguments are required: -f/--file, -c/--path-config, "
                  "-s/--path-config-sol6")
            return

        # Initialize the log and have the level set properly
        setup_logger(args.log_level)

        # Read the configs
        self.variables = self.read_configs(args.path_config, args.path_config_sol6)

        # Parse the yang specifications file into an empty dictionary
        self.parsed_dict = {}

        # Read the data from the provided yaml file into variables
        self.tosca_vnf, self.tosca_lines = self.read_tosca_yaml(args.file)

        # Determine what provider to use
        self.provider = self.find_provider(args.provider, self.tosca_lines,
                                           self.supported_providers)
        if self.provider is None:
            raise ValueError("The TOSCA provider could not be automatically found, pass it in"
                             "manually.")
        self.provider = self.provider.lower()

        # Initialize the proper converter object for the given provider
        self.converter = self.initialize_converter(self.provider, self.supported_providers)

        # Try to convert variables to their actual values
        self.converter.convert_variables()

        # Do the actual converting logic
        cnfv = self.converter.convert(provider=self.provider)

        self.output(cnfv)

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
            if not os.path.exists(self.args.output):
                dirs = self.args.output
                # Get the path except the last
                dirs = "/".join(dirs.split("/")[0:-1])
                os.makedirs(dirs, exist_ok=True)

            with open(self.args.output, 'w') as f:
                f.writelines(json_output)

        if not self.args.output:
            sys.stdout.write(json_output)

    def read_tosca_yaml(self, file):
        # Read the tosca vnf into a dict from yaml format
        log.info("Reading TOSCA YAML file {}".format(file))
        file_read = open(file, 'rb').read()
        file_lines = open(file, 'rb').readlines()
        parsed_yaml = yaml.load(file_read)
        return parsed_yaml, file_lines

    def initialize_converter(self, sel_provider, valid_providers):
        # We found a proper provider, so we can start doing things
        log.info("Starting conversion with provider '{}'".format(sel_provider))
        return valid_providers[sel_provider](self.tosca_vnf, self.parsed_dict,
                                             variables=self.variables)

    @staticmethod
    def find_provider(arg_provider, file_lines, valid_providers):
        # Figure out what class we want to use
        # If it was specifically provided as a parameter
        if arg_provider:
            return arg_provider
        else:
            # Try to figure out what it is

            sel_provider = "-".join(Sol6Converter.find_provider(file_lines).split(" "))

            # If the provider is not a part of a valid provider, i.e. 'cisco' in ['cisco', 'nokia'],
            # check if any of the valid providers are in the sel_provider,
            #   i.e. 'cisco' in '&provider-cisco'
            if sel_provider not in valid_providers:
                for s_p in valid_providers:
                    if s_p in sel_provider:
                        return s_p
                raise TypeError("Unsupported provider: '{}'".format(sel_provider))
            return sel_provider

    def interactive_mode(self):
        yn = ["y", "n"]
        args = self.args
        log_levels = {
            logging.NOTSET: "NOTSET",
            logging.DEBUG: "DEBUG",
            logging.INFO: "INFO",
            logging.WARNING: "WARNING",
            logging.ERROR: "ERROR",
            logging.CRITICAL: "CRITICAL"
        }
        log_level_str = dict_utils.reverse_dict(log_levels)

        print("--Interactive Mode Started--")

        # ** Initiate logging **
        setup_logger(args.log_level)

        print("Select log level")
        print("Log level set to {}.".format(log_levels[args.log_level]))

        opt = self.valid_input("OK? (y/n)  ", yn)
        if opt == "n":
            levels = list(log_level_str.keys())
            level = self.valid_input("Choose log level: {}: ".format(levels), levels)
            setup_logger(level)

        # ** Read the config file locations **
        while True:
            if not args.path_config or not args.path_config_sol6:
                print("Select config files")
            if not args.path_config:
                tosca_config = self.valid_input_file("TOSCA Config file (.toml)")
            else:
                tosca_config = args.path_config
            if not args.path_config_sol6:
                sol6_config = self.valid_input_file("SOL6 Config file (.toml)")
            else:
                sol6_config = args.path_config_sol6

            print("TOSCA Config: {}".format(tosca_config))
            print("SOL6  Conifg: {}".format(sol6_config))
            opt = self.valid_input("OK? (y/n)", yn)
            if opt == "y":
                break
        self.variables = self.read_configs(tosca_config, sol6_config)

        # ** Parse the yang specifications file into an empty dictionary **
        self.parsed_dict = {}

        # Read the data from the provided yaml file into variables
        while True:
            if not args.file:
                print("Select input file")
                tosca_file = self.valid_input_file("TOSCA input file (.yaml)")
            else:
                tosca_file = args.file

            print("TOSCA File: {}".format(tosca_file))
            opt = self.valid_input("OK? (y/n)", yn)
            if opt == "y":
                break
        self.tosca_vnf, self.tosca_lines = self.read_tosca_yaml(tosca_file)

        # ** Output to a file (or not) **
        file_out = args.output
        set_file = False
        while True:
            if not file_out:
                # Only display this the first time
                if not set_file:
                    opt = self.valid_input("Set output file? (y/n)", yn)

                if opt == "y" or set_file:
                    print("Specify file (.json)")
                    file_out = input("? ")
            print("Output file: {}".format(file_out))
            opt = self.valid_input("OK? (y/n)", yn)
            if opt == "y":
                break
            set_file = True
            file_out = None
        self.args.output = file_out

        # ** Determine what provider to **
        while True:
            if not args.provider:
                found_prov = None
                try:
                    found_prov = self.find_provider(None, self.tosca_lines,
                                                    self.supported_providers)
                except KeyError:
                    pass

                if found_prov:
                    print("Found provider '{}'".format(found_prov))
                    opt = self.valid_input("OK? (y/n)", yn)
                    if opt == "y":
                        break

                found_prov = self.valid_input(
                    "Select provider from list: '{}'".format(list(self.supported_providers.keys())),
                    list(self.supported_providers.keys()))

                print("Provider: '{}'".format(found_prov))
                cont = self.valid_input("OK? (y/n)", yn)
                if cont == "y":
                    break
        self.provider = found_prov

        # ** Initialize the proper converter object for the given provider **
        self.converter = self.initialize_converter(self.provider, self.supported_providers)

        # ** o the actual converting logic **
        cnfv = self.converter.convert(provider=self.provider)

        self.output(cnfv)

    @staticmethod
    def valid_input_file(prompt):
        """
        Only accept the input if the file specified exists
        """
        while True:
            print(prompt)
            choice = input("? ")
            if os.path.isfile(choice):
                return choice
            else:
                print("Error: File not found")

    @staticmethod
    def valid_input(prompt, opts):
        """
        Convert all input to lowercase to check validity
        :param prompt:
        :param opts:
        :return: Original item that the input matches
        """
        opts_l = list(map(str.lower, opts))
        while True:
            print(prompt)
            choice = input("? ")
            if choice.lower() in opts_l:
                return opts[opts_l.index(choice.lower())]


def setup_logger(log_level=logging.INFO):
    log_format = "%(levelname)s - %(message)s"
    log_folder = "logs"
    log_filename = log_folder + "/solcon.log"
    # Ensure log folder exists
    if not os.path.exists(log_filename):
        os.mkdir(log_folder)

    logging.basicConfig(level=log_level, filename=log_filename, format=log_format)
    # Duplicate the output to the console as well as to a file
    console = logging.StreamHandler()
    console.setLevel(log_level)
    console.setFormatter(logging.Formatter(log_format))
    logging.getLogger().addHandler(console)


if __name__ == '__main__':
    SolCon()
