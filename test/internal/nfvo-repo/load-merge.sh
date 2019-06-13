#!/usr/bin/env bash
cd $(dirname $0)
root=../../..
export PYTHONPATH=$root/src

# Run all files in $example_root
output_root=$root/outputs/nfvo-repo

for filename in $output_root/*.json; do
    file=$(basename $filename)
    echo Load merge $file...
    ncs_load -lm -F o $output_root/$file
done
