#!/usr/bin/env python3
"""

"""
__author__ = "Aaron Steele"
__credits__ = ["Frederick Jansson"]
__version__ = "0.8.0"

import argparse
import json
import yaml
import logging
import sys
import os.path
from utils import dict_utils
from converters.sol6_converter import Sol6Converter
from converters.sol6_converter_cisco import SOL6ConverterCisco
from converters.sol1_converter import Sol1Converter
from src.sol6_config_default import SOL6ConfigDefault
import toml
log = logging.getLogger(__name__)


class SolCon:
    def __init__(self, internal_run=False, internal_args=None):
        self.variables = None
        self.tosca_lines = None
        self.tosca_vnf = None
        self.converter = None
        self.provider = None
        self.supported_providers = None
        self.cnfv = None

        if internal_args and internal_args["e"] is False:
            print("Starting SolCon (v{})...".format(__version__))

        self.desc = "NFVO SOL6 Converter (SolCon): Convert a SOL001 (TOSCA) YAML to SOL006 JSON"

        self.supported_providers = {
            "cisco": SOL6ConverterCisco,
            "mavenir": SOL6ConverterCisco
        }

        parser = argparse.ArgumentParser(description=self.desc)
        parser.add_argument('-f', '--file',
                            help="The VNF YAML/JSON file to be processed")
        parser.add_argument('-o', '--output',
                            help="The output file for the convtered VNF (JSON/YAML format), "
                                 "outputs to stdout if not specified")
        parser.add_argument('-l', '--log-level',
                            choices=['DEBUG', 'INFO', 'WARNING'], default=logging.INFO,
                            help="Set the log level for standalone logging")
        # parser.add_argument('-n', '--dry-run', action='store_true', help="Don't send VNFD to NSO")
        parser.add_argument('-c', '--path-config',
                            help='Location of the paths configuration file for TOSCA paths '
                                 '(TOML format)')
        parser.add_argument('-s', '--path-config-sol6',
                            help='Location of the paths configuration file for SOL6 paths (OPTIONAL) '
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
        parser.add_argument('-e', '--output-silent', action='store_true', default=False,
                            help=argparse.SUPPRESS)

        args = parser.parse_args()
        if internal_run:
            args.file = internal_args["f"]
            args.output = internal_args["o"]
            args.path_config = internal_args["c"]
            if "s" in internal_args:
                args.path_config_sol6 = internal_args["s"]
            args.provider = internal_args["r"]
            args.log_level = internal_args["l"]
            args.output_silent = internal_args["e"]

        self.args = args
        self.parser = parser

        if args.interactive:
            self.interactive_mode()
            return

        # Determine if the file we're converting is tosca or sol6 based on the file extension
        is_yaml = args.file.split(".")[-1].lower() == "yaml"

        if not args.file or (not args.path_config and not is_yaml):
            print("error: the following arguments are required: -f/--file, -c/--path-config")
            return

        sol6_config_isfile = True
        if not args.path_config_sol6:
            args.path_config_sol6 = SOL6ConfigDefault.config
            sol6_config_isfile = False

        # Initialize the log and have the level set properly
        setup_logger(args.log_level)

        # Read the configs
        self.variables = self.read_configs(args.path_config, args.path_config_sol6, sol6_config_isfile)

        # Parse the yang specifications file into an empty dictionary
        self.parsed_dict = {}

        if is_yaml:
            # Read the data from the provided yaml file into variables
            self.tosca_vnf, self.tosca_lines = self.read_input_file(args.file, is_yaml)

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
            self.cnfv = self.converter.convert(provider=self.provider)
        else:
            # Read the data from the provided yaml file into variables
            self.sol6_vnf, self.sol6_lines = self.read_input_file(args.file, is_yaml)
            converter = Sol1Converter(self.sol6_vnf, self.parsed_dict, self.variables)
            self.cnfv = converter.convert()

        self.output()

    @staticmethod
    def read_configs(tosca_config, sol6_config, sol6_is_file=True):
        # Read the path configuration file
        variables = toml.load(tosca_config)
        if sol6_is_file:
            variables_sol6 = toml.load(sol6_config)
        else:
            variables_sol6 = toml.loads(sol6_config)

        return dict_utils.merge_two_dicts(variables, variables_sol6)

    def output(self):
        output_lines = None
        # Prune the empty fields
        if self.args.prune:
            self.cnfv = dict_utils.remove_empty_from_dict(self.cnfv)

        # Output with yaml.dump if our output file is yaml
        if self.args.output and self.args.output.split(".")[-1].lower() == "yaml":
            output_lines = yaml.dump(self.cnfv, default_flow_style=False)
        else:
            # Put the data:esti-nfv:vnf tags at the base
            cnfv = {'data': {'etsi-nfv-descriptors:nfv': self.cnfv}}

            output_lines = json.dumps(cnfv, indent=2)

        # Get the absolute path, since apparently relative paths sometimes have issues with things?
        if self.args.output:
            abs_path = os.path.abspath(self.args.output)
            # Also python has a function for what I was sloppily doing, so use that
            abs_dir = os.path.dirname(abs_path)
            if not os.path.exists(abs_dir):
                os.makedirs(abs_dir, exist_ok=True)

            with open(self.args.output, 'w') as f:
                f.writelines(output_lines)

        if not self.args.output and not self.args.output_silent:
            sys.stdout.write(output_lines)

    @staticmethod
    def read_input_file(file, is_yaml):
        log.info("Reading TOSCA {} file {}".format("YAML" if is_yaml else "JSON", file))
        f = open(file, 'rb')
        file_read = f.read()
        f.close()
        f = open(file, 'rb')
        file_lines = f.readlines()
        f.close()
        if is_yaml:
            parsed = yaml.safe_load(file_read)
        else:
            parsed = json.loads(file_read)

        return parsed, file_lines

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

            # If the provider is not a part of a valid provider, i.e. 'cisco' in ['cisco'],
            # check if any of the valid providers are in the sel_provider,
            #   i.e. 'cisco' in '&provider-cisco'
            if sel_provider not in valid_providers:
                for s_p in valid_providers:
                    if s_p in sel_provider:
                        return s_p
                # No supported provider was found, try running it with the cisco one to see if it works, since
                # the config files might have been edited
                log.error("Unsupported provider: '{}', running with default provider 'cisco'. THIS WILL PROBABLY FAIL."
                          .format(sel_provider))
                sel_provider = 'cisco'
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
            sol6_config_isfile = True

            if not args.path_config or not args.path_config_sol6:
                print("Select config files")
            if not args.path_config:
                tosca_config = self.valid_input_file("TOSCA Config file (.toml)")
            else:
                tosca_config = args.path_config
            if not args.path_config_sol6:
                # Handle if they want to use the default config
                opt = self.valid_input("Specify sol6 config file? (optional) (y/n)", yn)
                if opt == "y":
                    sol6_config = self.valid_input_file("SOL6 Config file (.toml)")
                else:
                    sol6_config = SOL6ConfigDefault.config
                    sol6_config_isfile = False

            else:
                sol6_config = args.path_config_sol6

            print("TOSCA Config: {}".format(tosca_config))
            print("SOL6  Conifg: {}".format(sol6_config))
            opt = self.valid_input("OK? (y/n)", yn)
            if opt == "y":
                break
        self.variables = self.read_configs(tosca_config, sol6_config, sol6_config_isfile)

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
        self.tosca_vnf, self.tosca_lines = self.read_input_file(tosca_file)

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
