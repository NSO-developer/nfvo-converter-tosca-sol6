#!/usr/bin/env bash
cd $(dirname $0)

for d in */ ; do
    echo Execute Directory $d run.sh
    $d/run.sh
done
