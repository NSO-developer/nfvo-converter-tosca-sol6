# TOSCA (SOL001) to SOL006 VNFD Converter
Can be run as a package in NSO: 

    NSO command to be put here

Also can be run standalone:

    python3 tosca.py -f examples/standalone_vpc_vnfd_esc_4_4.yaml --dry-run -y etsi-nfv-vnf.yang

### TOSCA VNFD Relationships

![TOSCA VNFD Relationships](TOSCA-vnfd-relations.png)

### USAGE
**Standalone**
tosca.py is the entry point for the standalone version of the converter.



**Arguments**
- -f --file (REQ): The TOSCA VNF YAML file to be processed
- -o --output: The name of the file to be output in JSON format
- -l --log-level: Set the log level for NSO and standalone logging
- -H --hide-output: By default the tool will output the processed JSON at the end, specify this flag to stop that
- -n --dry-run: Don't send the converted information to NSO
- -y --yang-template (REQ): The given YANG specifications file for the tool to fill out
- -g --no-grouping: If there are no grouping tags in the YANG specifications file give this tag,
                  otherwise it will fail to parse the file
- -p --prune: Prune empty values from the dict at the end


### DATA STRUCTURES


### ALGORITHMS
