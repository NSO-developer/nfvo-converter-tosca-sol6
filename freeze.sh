#!/usr/bin/env bash

echo Creating build file...
if [[ -d "dist" ]]; then
  rm -r dist
fi
pyinstaller -F -p python/nfvo_solcon_tosca solcon.py
