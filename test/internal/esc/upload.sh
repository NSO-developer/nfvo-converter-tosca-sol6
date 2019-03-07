#!/usr/bin/env bash
root=../../..
output_dir=$root/outputs/esc

for filename in $output_dir/*.json; do
    scp $filename $anu_vm:~/aaron/esc
done
