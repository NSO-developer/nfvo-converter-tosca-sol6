
class EtsiNfvVnfd:
    """
    A data class based on the SOL006 structure to be loaded for conversion

    I don't think this is actually neeeded.
    We already have a dict with all this information in the proper structure coming in anyway
    So I think this would be most helpful if we made a sol1 version intead of sol6
    """

    def __init__(self):
        self.vnfd = {
            # Non-containers
            "id": None,
            "provider": None,
            "product_name": None,
            "software_version": None,
            "version": None,
            "product_info_name": None,
            "product_info_desc": None,
            "vnfm_info": None,
            "localization_settings": None,
            "default_localization_language": None,
            "auto_scale": None,
            # Containers
            "vdu": {
                "id": None,
                "name": None,
                "description": None,
                "boot-data": None,
                "configurable-properties": {},
                "monitoring-parameter": {
                    "id": None,
                    "name": None,
                    "collection-period": None,
                    "performance-metric": None
                },
                "nfvi-constraint": None,
                "sw-image-desc": None,
                "boot-order": {},
                "virtual-storage-desc": None,
                "virtual-compute-desc": None,

                "int-cpd": {
                    "id": None,
                    "int-virtual-link-desc": None,
                    "bitrate-requirement": None,
                    # Uses virtual-network-interface-requirements, verify
                    "nicio-requirements": None,
                    "order": None,
                    # Uses cpd
                    "security-group-rule-id": None
                }
            },
            "virtual_compute_desc": {},
            "virtual_storage_desc": {},
            "sw_image_desc": {},
            "int_virtual_link_desc": {},
            "security_group_rule": {},
            "ext_cpd": {},
            "df": {},
            "configurable_propereties": {},
            "modifiable_attributes": {},
            "lifecycle_management_script": {},
            "element_group": {},
            "indicator": {}
        }


class ToscaVnfd:
    """
    Data class for conversion.
    It's all a dict for ease of yaml.dump
    """
    def __init__(self):
        self.vnfd = {
            "topology_template": {
                "node_templates": {
                    "vnf": {
                        "type": None,

                        "properties": {
                            # Cisco extension + default tosca
                            "descriptor_id": None,
                            "descriptor_version": None,
                            "provider": None,
                            "software_version": None,
                            "product_info_name": None,
                            "product_info_description": None,
                            "product_name": None,
                            "flavour_id": None,
                            "flavour_description": None,
                            "vnfm_info": [],
                            "configurable_properties": {},
                            "lcm_operations_configuration": {},
                            "localization_languages": None,
                            "default_localization_languages": None,
                            "modifiable_attributes": None,
                            "monitoring_parameters": None,
                            "vnf_profile": None
                        },
                        "interfaces": {
                            "Vnflcm": {}
                        }
                    },
                    # Number will be filled in later
                    "vdu_": {
                        "type": "cisco.nodes.nfv.Vdu.Compute",
                        "properties": {
                            "name": None,
                            "description": None,
                            "boot_order": {},
                            "configurable_properties": {
                                "additional_vnfc_configurable_properties": {},
                            },
                            "vdu_profile": {
                                "max_number_of_instances": None,
                                "min_number_of_instances": None
                            }
                        },
                        "capabilities": {
                            "virtual_compute": {
                                "properties": {
                                    "virtual_cpu": {
                                        "num_virtual_cpu": None
                                    },
                                    "virtual_memory": {
                                        "virtual_mem_size": None
                                    }
                                }
                            }
                        },
                        "requirements": [
                            {"virtual_storage": None}
                        ]
                    }
                }
            }
        }
        # That's just for reference, don't actually use it
        self.vnfd = {}
