#!/usr/bin/env bash
export PYTHONPATH=../../python/nfvo_solcon_tosca

# Run the four examples that the program shouldn't *at least* crash with
tosca=../../solcon.py
config=../../config.toml
vpc_vnfd=../../examples/standalone_vpc_vnfd_esc_4_4.yaml
vcu=../../examples/altiostar_vCU.yaml
vdu=../../examples/altiostar_vDU.yaml
vpec=../../examples/VPEC_SI_UPP_vnfd_esc_4_4.yaml
echo Run $vpc_vnfd...
python3 $tosca -f $vpc_vnfd -o ../../outputs/output_esc.json -c $config
echo Run $vdu...
python3 $tosca -f $vcu -o ../../outputs/output_vCU.json -c $config
echo Run $vdu...
python3 $tosca -f $vdu -o ../../outputs/output_vDU.json -c $config
echo Run $vpec...
python3 $tosca -f $vpec -o ../../outputs/output_VPEC_SI.json -c $config
