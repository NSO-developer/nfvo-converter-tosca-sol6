# SolCon: TOSCA (SOL001) to SOL006 VNFD Converter
Can be run as a package in NSO, eventually: 
```
    NSO command to be put here
```
Also can be run standalone:
```
    PYTHONPATH=python/nfvo_solcon_tosca
    python3 solcon.py -f examples/standalone_vpc_vnfd_esc_4_4.yaml -o output.json -c config-esc.toml -s config-sol6.coml
```
### TOSCA VNFD Relationships

![TOSCA VNFD Relationships](TOSCA-vnfd-relations.png)

### USAGE
**Standalone**  
`solcon.py` is the entry point for the standalone version of the converter.  
`config-esc.toml` has the default and configurable paths and values for TOSCA ESC.
`config-sol6.toml` has the default and configurable paths and values for SOL6.


**Arguments**
- -f --file (REQ): The TOSCA VNF YAML file to be processed
- -o --output: The name of the file to be output in JSON format, outputs to stdout if not specified
- -c --path-config (REQ): Location of the paths configuration file for TOSCA paths (TOML format)
- -s --path-config-sol6 (REQ): Location of the paths configuration file for SOL6 paths (TOML format)
- -l --log-level: Set the log level for standalone logging
- -p --prune: Do not prune empty values from the dict at the end
- -r --provider: Specifically provide the provider instead of trying to
                        read it from the file. (Supported providers here when run in program)
- -i --interactive: Initiate the interactive mode for the program
- -h --help: Show the help message

**Wiki**  
See https://confluence-eng-sjc1.cisco.com/conf/display/NSOUS/TOSCA+to+SOL006+Converter


### Current Limitations
* Scaling aspects are not converted at this time
* Only the default instantiation level is supported in ESC VNFDs
