#!/usr/bin/env bash
cd $(dirname $0)

for d in */ ; do
    echo Execute Directory $d load-merge.sh
    $d/load-merge.sh
done
