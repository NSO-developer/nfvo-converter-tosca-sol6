#!/usr/bin/env bash
root=../../..
export PYTHONPATH=$root/python/nfvo_solcon_tosca

# Run all files in $example_root
tosca=$root/solcon.py
output_dir=$root/outputs
config_tosca=$root/config/config.toml
config_sol6=$root/config/config-sol6.toml
example_root=$root/examples/

for filename in $example_root/*.yaml; do
    echo Run $filename
    python3 $tosca -f $filename -o "$output_dir/${filname%.yaml}.json" -c $config_tosca -s $config_sol6

done

