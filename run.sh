#!/usr/bin/env bash
export PYTHONPATH=python/tailf_etsi_rel2_nfvo_tosca

# Run the four examples that the program shouldn't *at least* crash with
/usr/local/bin/python3 tosca.py -f examples/standalone_vpc_vnfd_esc_4_4.yaml -o output_esc.json --dry-run -y etsi-nfv-vnf.yang -H
/usr/local/bin/python3 tosca.py -f examples/altiostar_vCU.yaml -o output_vCU.json --dry-run -y etsi-nfv-vnf.yang -H
/usr/local/bin/python3 tosca.py -f examples/altiostar_vDU.yaml -o output_vDU.json --dry-run -y etsi-nfv-vnf.yang -H
/usr/local/bin/python3 tosca.py -f examples/VPEC_SI_UPP_vnfd_esc_4_4.yaml -o output_VPEC_SI.json --dry-run -y etsi-nfv-vnf.yang -H
