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

###Idea 1
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
for map_tosca, map_sol6 in maps, if valid map:
    for tosca, sol6 in vdu_mapping:
        set_path_to(map_tosca.format(tosca), path_to_value(map_sol6.format(sol6)))

        Which would translate to
        set_path_to(tosca_vdu_name.format("c1"), path_to_value(sol6_vdu_name.format(0)
        ->
        set_path_to("topology_template.node_template.{}.properties.name".format("c1"),
                    path_to_value("vnfd.vdu.{}.name".format("0")))
```

The key difficulties in this approach would be
1) Determining if the mapping is valid for the given path/value in the TOSCA YAML
2) Ensuring mapping between tosca and sol6 always made sense
3) Handling if the mapping is not valid for all elements
