I'm going to try another idea for mapping values with the VDUs, since they can be
considered their own, effectively separate, subsection of the entire data structures

###The problem
There is data embedded in a structure in a multi-tiered dict T, we need to move the data
from its' current location and rearrange it into new locations, sometimes in very different
locations, and sometimes not.

YAML does not specify that the keys of dicts or lists need to be predefined or consistent
in any way.
Thus we can only occasionally assume that the structure can be known.
More often, there are other, interior, values that are better for identification of certain
types of data, most used are the `type` field.

For example, connection points
```
c1_nic0:
  type: cisco.nodes.nfv.VduCp
```
The name is arbitrary, but the type is not.

It might be that making an automatic mapping that is able to handle this kind of complicated
behavior would just be better represented in raw code, but there are a lot of duplicate
parts of code in what I have already written, and there must be a better way to do this.

###V2 Mapping
Have keys, as is given in current TOSCA and SOL6 classes, but instead of automatically mapping
variables with the same name, be able to give a dict/some kind of relation between two arbitrary
variables.

For example:
```
tosca_id = ".vnfd.id"
sol6_id = ".vnf.properties.id"
maps = {tosca_id: sol6_id,
        ...
}
```

Then if a valid path is found while scanning through the file, apply `set_path_to(path_to_value(key), value))`

This effectively duplicates the existing functionality in the two classes, although with
a bit of an extension, since we should be able to have many-to-one and one-to-many mappings.
But what about instantiations of objects?
```
tosca_vdu_name = "topology_template.node_template.{c1}.properties.name"
sol6_vdu_name = "vnfd.vdu.[0].name"
```
The primary difficulty here is mapping
```
    c1 -> vdu[0]
    c2 -> vdu[1]
    s3 -> vdu[2]
    s4 -> vdu[4]
```
Given that the names can be arbitrary and there can be an arbitrary amount of them.

Perhaps before starting value mapping, define a mapping function for the VDUs, or general for
any list of values in the TOSCA YAML.

```
vdu_mapping = generate_map(type="cisco.nodes.nfv.Vdu.Compute",
                           path="topology_template.node_template",
                           map_type=int, map_start=0)
        -> {"c1": 0, "c2": 1, "s3": 2, "s4": 3}
```

Then, the previous definition could be
```
tosca_vdu_name = "topology_template.node_template.{}.properties.name"
sol6_vdu_name = "vnfd.vdu.{}.name"

maps = {tosca_vdu_name: sol6_vdu_name
}
```

Then to apply the mapping
```
for map_tosca, map_sol6 in maps:
    for tosca, sol6 in vdu_mapping:
        set_path_to(map_tosca.format(tosca), path_to_value(map_sol6.format(sol6)))

        Which would translate to
        set_path_to(tosca_vdu_name.format("c1"), path_to_value(sol6_vdu_name.format(0)
        ->
        set_path_to("topology_template.node_template.{}.properties.name".format("c1"),
                    path_to_value("vnfd.vdu.{}.name".format("0")))
```

####Mapping Syntax
```
    (TOSCA_PATH, (Single flag or tuple of flags)):  SOL6_PATH [, MAPPING]
```
The SOL6_PATH can be alone, but if a mapping is required then the value must be a list with the path as the first
element and the mapping as the second.

###Mapping arbitrary number of variables
The problem is the need to map lists inside of VDUs. There is currently not a way
to do that with the system I have set up.

Example problem
```
<vdu>
    <id>c1</id>
    <int-cpd>
        <id>c1_nic0</id>
        <virtual-link-descriptor>etsi-vpc-di-internal1</virtual-link-descriptor>
        <layer-protocol>IPv4</layer-protocol>
        <interface-id xmlns="http://tail-f.com/pkg/tailf-etsi-rel3-nfvo-vnfm">0</interface-id>
        <additional-parameters xmlns="http://tail-f.com/pkg/tailf-etsi-rel3-nfvo-vnfm">
        <allowed-address-variable>C1_NICID_0_ALLOWED_ADDRS</allowed-address-variable>
        </additional-parameters>
    </int-cpd>
</vdu>
```

Where there need to be multiple internal connection point descriptors.

```
# Generate VDU map
vdu_map = self.generate_map(T.node_template, T.vdu_identifier[0], T.vdu_identifier[1])
    -> {'c1': 0, 'c2': 1, 's3': 2, 's4': 3}
    
tosca_int_cpd_id = "topology_template.node_template.{c1_nic0}"
sol6_int_cpd_id  = "vnfd.vdu.[0].[0].id"
    cp_to_vdu = c1_nic0.requirements.virtual_binding = c1
    
    vdu[vdu_map[cp_to_vdu]] (vdu[0]) ->
        c1_nic0 -> [0]
        c1_nic1 -> [1]
    
    vdu[1] ->
        c2_nic0 -> [0]
        c2_nic1 -> [1]
    
    loop over CPs:
        map cp to vdu
        cp_map = generate_map() 
            -> "c1_nic0": "c1"
               "c1_nic1": "c1"
               "c2_nic0": "c2"
               "c2_nic1": "c2"
        
    loop over vdus:
        0:
            find CPs for this vdu
            cps = filter(cp_map if value == vdu_map[value=0])
                -> "c1_nic0": "c1"
                   "c1_nic1": "c1"
```


The solution for this is to change how maps are represented. The new map data structure is
```
    MapElem(name, cur_map, parent_map)
```
What this means is it is now possible to store an arbitrary amount of depth in a single map.

For our previous example, the map would now look like this
```
    cp_map = generate_map()
        ->  MapElem("c1_nic0", 0, parent=MapElem("c1", 0))
            MapElem("c1_nic1", 1, parent=MapElem("c1", 0))
            MapElem("c2_nic0", 0, parent=MapElem("c2", 1))
            MapElem("c2_nic1", 1, parent=MapElem("c2", 1))
```

Which allows iterative behavior no matter how deep the mapping goes.
