#!/usr/bin/env bash
export PYTHONPATH=python/tailf_etsi_rel2_nfvo_tosca

# Run the four examples that the program shouldn't *at least* crash with
vpc_vnfd=examples/standalone_vpc_vnfd_esc_4_4.yaml
vcu=examples/altiostar_vCU.yaml
vdu=examples/altiostar_vDU.yaml
vpec=examples/VPEC_SI_UPP_vnfd_esc_4_4.yaml
echo Run $vpc_vnfd...
/usr/local/bin/python3 tosca.py -f $vpc_vnfd -o outputs/output_esc.json --dry-run -y etsi-nfv-vnf.yang -H -p
echo Run $vdu...
/usr/local/bin/python3 tosca.py -f $vcu -o outputs/output_vCU.json --dry-run -y etsi-nfv-vnf.yang -H -p
echo Run $vdu...
/usr/local/bin/python3 tosca.py -f $vdu -o outputs/output_vDU.json --dry-run -y etsi-nfv-vnf.yang -H -p
echo Run $vpec...
/usr/local/bin/python3 tosca.py -f $vpec -o outputs/output_VPEC_SI.json --dry-run -y etsi-nfv-vnf.yang -H -p
