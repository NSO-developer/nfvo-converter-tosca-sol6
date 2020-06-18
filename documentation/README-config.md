# SOLCon Configuration Options

Variables in TOSCA and SOL6 classes have been switched to reading from a config file

```
[tosca]    
    topology_template = "topology_template"    
    node_templates = ["topology_template", "node_templates"]
```

Needed a way to specify deep paths without repeating too many strings
```
[tosca]
    root = "root_value"
    child_of_root = ["root", "child_path_name"]
```
This example would create a path heirarchy that looks like
```
    root_value.child_path_name
````

Providers have different types for the instantiations of blocks of code
We needed a way to support finding different blocks of code without recompiling

```
providers=["cisco", "prov2"]

[provider-identifiers.cisco]    
    vdu = ["type", "cisco.nodes.nfv.Vdu.Compute"]    
    int-cpd = ["type", "cisco.nodes.nfv.VduCp"]

[provider-identifiers.prov2]    
    vdu = ["type", "prov2.nodes.nfv.Vdu.Compute"]
    int-cpd = ["type", "prov2.nodes.nfv.VduCp"]

```

If the configuration file has items that the program does not use, it will just ignore them.

On the other hand, if the program expects a configuration value in the file and does not find it, a warning
will be displayed, but the program will continue as much as it can with the other mappings that have been
specified.

**Note**  
If there is a variable postfixed with `_VAL`, that means it will not be parsed for the path
heirarchy, but will instead just be set to the value in the configuration file.
