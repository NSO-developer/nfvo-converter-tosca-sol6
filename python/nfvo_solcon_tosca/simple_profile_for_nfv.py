import logging
import re

log = logging.getLogger(__name__)


def _verify(vnfd):
    if vnfd.get("tosca_definitions_version", '') != \
            "tosca_simple_profile_for_nfv_1_0_0":
        raise ValueError("Version not tosca_simple_profile_for_nfv_1_0_0")


def _vnfd_id(tosca_vnf):
    return tosca_vnf['metadata']['template_name']


def _layer_protocol(lp):
    if lp == "ipv4":
        return "tailf-etsi-rel2-nfvo:IPv4"
    elif lp == "ipv6":
        return "tailf-etsi-rel2-nfvo:IPv6"


def _get_vnf(nt):
    for _, node in nt.items():
        if node['type'].startswith('tosca.nodes.nfv.VNF'):
            return node

    return None


def _get_external_cp(nt):
    vnf = _get_vnf(nt)

    if not vnf:
        raise ValueError("No VNF element found")

    cp = []
    i2e = {}
    for req in vnf['requirements']:
        vl = req.get('virtual_link', [])
        if vl:
            vl_type = vl[1]
            name = vl[0]
            if vl_type == 'external_virtual_link':
                if name not in nt:
                    raise ValueError("No external CP named {}".format(name))
                extcp = nt[name]
                lp = _layer_protocol(extcp['properties']['layer_protocol'])
                # TODO: management
                cp.append({
                    'id': name,
                    'layer-protocol': lp
                })

                # Check for pointer to internal CP
                for req in extcp.get('requirements', []):
                    if 'internal_connection_point' in req:
                        i2e[req['internal_connection_point']] = name
    return (cp, i2e)


def _get_dep_flavors(vnf):
    dep_f = vnf['capabilities']['deployment_flavour']

    vdu_names = []
    vdu_profiles = []

    properties = dep_f['properties']
    vdu_names = properties['vdu_profile'].keys()
    for name in vdu_names:
        vdu_p = properties['vdu_profile'][name]
        vdu_profiles.append({
            'vdu': name,
            'min-number-of-instances': vdu_p['min_number_of_instances'],
            'max-number-of-instances': vdu_p['max_number_of_instances'],
        })

    inst_levels = []
    for name, il in properties['instantiation_levels'].items():
        il_vdu_levels = []
        for vdu_name, vdu_l in il['vdu_levels'].items():
            il_vdu_levels.append({
                'vdu': vdu_name,
                'number-of-instances': vdu_l['number_of_instances']
            })

        inst_levels.append({
            'id': name,
            'vdu-level': il_vdu_levels
        })

    deployment_flavor = {
        'id': properties['flavour_id'],
        'vdu-profile': vdu_profiles,
        'instantiation-level': inst_levels,
        'default-instantiation-level':
            properties['default_instantiation_level_id']
    }
    return ([deployment_flavor], vdu_names)


def _get_virtual_storage(nt, idx, name):
    vs = nt[name]
    # TODO: Fix type
    if 0 == idx:
        s_type = "root"
    elif 1 == idx:
        s_type = "ephemeral"
    return {
        'id': name,
        'type-of-storage': s_type,
        'size-of-storage': vs['properties']['size_of_storage']
    }


def _str_to_gb(s):
    regb = r"(\d+)\s*GB"
    m = re.match(regb, s)
    if m:
        return m.group(1)


def _vdu_nics(nt, vdu_name, intcp2extcp):
    icps = []
    virtual_link_names = set()
    for name, obj in nt.items():
        if obj['type'] != 'tosca.nodes.nfv.Cpd.CiscoESC':
            continue
        # log.info(obj['requirements'])
        valid_binding = False
        virtual_link = None
        for req in obj['requirements']:
            if 'virtual_binding' in req:
                valid_binding = req['virtual_binding'] == vdu_name
            elif 'virtual_link' in req:
                virtual_link = req['virtual_link']

        if not valid_binding:
            continue

        if virtual_link is None and \
                name not in intcp2extcp:
            continue

        properties = obj['properties']
        lp = _layer_protocol(properties['layer_protocol'])
        cp = {
            'id': name,
            'layer-protocol': lp,
            'tailf-etsi-rel2-nfvo-esc:interface-id':
            properties['cisco_esc_properties']['nicid']
        }
        if name in intcp2extcp:
            cp['external-connection-point-descriptor'] = intcp2extcp[name]
        else:
            cp['virtual-link-descriptor'] = virtual_link
            virtual_link_names.add(virtual_link)
            log.debug('nic %s virtual_link %s', name, virtual_link)

        icps.append(cp)
    return (icps, virtual_link_names)


def _get_vdus(nt, vdu_names, intcp2extcp):
    vdus = []
    vcds = []
    vsds = []
    virtual_link_names = set()
    for name in vdu_names:
        vdu = nt[name]

        capas = vdu['capabilities']
        vc = capas['virtual_compute']['properties']
        mem_size = _str_to_gb(vc['virtual_memory']['virtual_mem_size'])
        vcds.append({
            'id': name,
            'virtual-memory': {
                'virtual-memory-size': mem_size
            },
            "virtual-cpu": {
                "number-of-virtual-cpus":
                vc['virtual_cpu']['num_virtual_cpu']
            }
        })

        vs_idx = 0
        vsds_names = []
        # log.info('vdu: %s - %s', name, str(vdu))
        for req in vdu.get('requirements', []):
            if 'virtual_storage' in req:
                vsds_names.append(req['virtual_storage'])
                vsds.append(_get_virtual_storage(nt,
                                                 vs_idx,
                                                 req['virtual_storage']))
                vs_idx = vs_idx + 1

        sid = {}
        for art in vdu.get('artifacts', []):
            if 'sw_image' in art:
                swi = art['sw_image']
                sid = {
                    "container-format": swi['container_format'],
                    "disk-format": swi['disk_format'],
                    "image": swi['sw_image'],
                }

        (icps, vls) = _vdu_nics(nt, name, intcp2extcp)
        virtual_link_names.update(vls)

        cisco_vdu = {
            'id': name,
            'internal-connection-point-descriptor': icps,
            'virtual-compute-descriptor': name,
            'virtual-storage-descriptor': vsds_names,
        }

        if sid != {}:
            cisco_vdu['software-image-descriptor'] = sid
        vdus.append(cisco_vdu)

    return (vdus, vcds, vsds, virtual_link_names)


def _get_virtual_links(nt, virtual_link_names):
    vls = []
    for name in virtual_link_names:
        vl = nt[name]
        log.info('vl %s = %s', name, vl)
        properties = vl['properties']
        log.info(properties)
        lp = _layer_protocol(properties['connectivity_type']['layer_protocol'])
        vls.append({
            'id': name,
            'description': properties.get('description', ''),
            'connectivity-type': {
                'layer-protocol': lp
            }
        })

    return vls


def tosca2cvnfd(tosca_vnf):
    _verify(tosca_vnf)

    nt = tosca_vnf["topology_template"]["node_templates"]
    vnf = _get_vnf(nt)

    if not vnf:
        raise ValueError("No VNF element found")

    # first get the external cp
    (extcp, intcp2extcp) = _get_external_cp(nt)

    # get Deployment flavors
    (dep_flavors, vdu_names) = _get_dep_flavors(vnf)

    # get VDUs
    (vdus, vcds, vsds, virtual_link_names) = _get_vdus(nt,
                                                       vdu_names,
                                                       intcp2extcp)

    vls = _get_virtual_links(nt, virtual_link_names)

    vnf_properties = vnf.get('properties', {})
    vnfd = {
        'id': _vnfd_id(tosca_vnf),
        'product-name': vnf_properties.get('product_name', ''),
        'version': vnf_properties.get('software_version', ''),
        'vdu': vdus,
        'virtual-compute-descriptor': vcds,
        'virtual-storage-descriptor': vsds,
        'tailf-etsi-rel2-nfvo:external-connection-point-descriptor': extcp,
        'deployment-flavor': dep_flavors,
    }

    if vls:
        vnfd['virtual-link-descriptor'] = vls

    return vnfd
