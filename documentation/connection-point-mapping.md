# Connection Point Mapping

SOL006 has a different mapping that's required for internal/external connection point mapping than previous versions.  
Now it is not possible to assign multiple internal connection point to a single external connection point directly. 
There must be a virtual link in between the two.

For example
```
    VNFD
        ext-cpd: ext_1
        ext-cpd: ext_2
    
        VDU 1
            int-cpd: int_1
            int-cpd: int_2
        VDU 2
            int-cpd: int_1
            int-cpd: int_2
```
If we want to connect all int_1 s to ext_1, we must do it like so
```
    VNFD
        int-virtual-link-desc: virt_1
        
        ext-cpd: ext_1
            int-virtual-link-desc: virt_1
        
        VDU 1
            int-cpd: int_1
                int-virtual-link-desc: virt_1
        
        VDU 2
            int-cpd: int_1
                int-virtual-link-desc: virt_1
```
So now the connections look like this
```
    | EXT_1 | ----> | VIRT_1 | <---- | VDU_1.int_1 |
                            ^------- | VDU_2.int_1 |
```

### TOSCA to SOL6
We are assuming there are only going to be two external connection points per VNFD in our conversion.  
The first will be for management (MGMT_CP) and the second for orchestration (ORCH_CP).  
All of the NICs with management: true will be assigned to the MGMT_CP, and everything else will be 
assigned to ORCH_CP.
```
    VNFD
        ext-cpd: ext_1
            int-virtual-link-desc: MGMT_CP
        ext-cpd: ext_2
            int-virtual-link-desc: ORCH_CP
        
        int-virtual-link-desc: MGMT_CP
        int-virtual-link-desc: ORCH_CP
    
        VDU 1
            int-cpd: int_1
                #TOSCA YAML: management: true
                int-virtual-link-desc: MGMT_CP
            int-cpd: int_2
                #TOSCA YAML: management: false
                int-virtual-link-desc: ORCH_CP
        VDU 2
            int-cpd: int_1
                #TOSCA YAML: management: false
                int-virtual-link-desc: ORCH_CP
            int-cpd: int_2
                #TOSCA YAML: management: true
                int-virtual-link-desc: MGMT_CP
```
