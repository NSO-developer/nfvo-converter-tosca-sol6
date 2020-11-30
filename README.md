# SolCon: TOSCA (SOL001) to SOL006 VNFD Converter
### TOSCA VNFD Relationships

![TOSCA VNFD Relationships](TOSCA-vnfd-relations.png)

### Introduction

This document outlines how to use the SolCon tool to convert TOSCA YAML SOL001 files to JSON SOL006
files to be able to load merge into NCS in Rel3 with the SOL6 VNFD model.  
For more detailed instructions, see the [User Guide](documentation/solcon-documentation.pdf).  
It is important to note that this tool is not expected to be able to convert a working SOL1 model to a 100% working SOL6 model.
The expectation is that the tool will do 80-90% of the work, and the last 10% be manually completed, as there are some things
the converter cannot handle. See the Limitations section for more detail.

### USAGE
#### Standalone
Console command:
```
    python solcon.py -f test-input.yaml -o output.json -c config/config-esc.toml
```
`solcon.py` is the entry point for the standalone version of the converter.  
`config-esc.toml` has the default and configurable paths and values for TOSCA ESC.
`config-sol6.toml` has the default and configurable paths and values for SOL6.

Converting from SOL6 to SOL1 is as simple as changing the input file to a JSON file, 
then switching the output file to a YAML file.
Example:
```
    python solcon.py -f output.json -o sol1-output.yaml -c config/config-esc.toml
```

#### Arguments
- -f --file (REQ): The TOSCA VNF YAML file to be processed
- -o --output: The name of the file to be output in JSON format, outputs to stdout if not specified
- -c --path-config (REQ): Location of the paths configuration file for TOSCA paths (TOML format)
- -l --log-level: Set the log level for standalone logging
- -p --prune: Do not prune empty values from the dict at the end
- -r --provider: Specifically provide the provider instead of trying to
                        read it from the file. (Supported providers here when run in program)
- -i --interactive: Initiate the interactive mode for the program
- -h --help: Show the help message

#### Documentation
- [User Guide](documentation/solcon-documentation.pdf)
- [Wiki](https://github.com/NSO-developer/nfvo-converter-tosca-sol6/wiki)

### Compatability
#### NFVO
| SolCon | NFVO Version |
| ---    | --- |
| 0.7.0 | 4.1.0 FCS |
| 0.6.1 - 0.6.2 | 4.0.0 FCS |
| 0.6    | pre-FCS |
| 0.5    | pre-FCS | 
#### TOSCA and SOL6
| Spec  | Version |
| ---   | --- |
| TOSCA | [ETSI GS NFV-SOL 001 V2.5.1 (2018-12)](https://www.etsi.org/deliver/etsi_gs/NFV-SOL/001_099/001/02.05.01_60/gs_NFV-SOL001v020501p.pdf) |
| SOL6  | revision 2019-03-18 |



### Limitations
* Any data not present in the TOSCA file will not be able to be generated for the SOL6 model.
* Internal connection points and external connection points must have unique names.
* Type extension and default values are not supported at this time.

This is an incomplete list of entries that need to be manually added to the converted file
* NSD
* External Networks
