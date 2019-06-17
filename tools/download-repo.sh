#!/bin/bash

# https://github.com/NSO-developer/nfvo-converter-tosca-sol6/archive/master.zip

if [ -f "solcon-master.zip" ]; then
  echo "'solcon-master.zip' found"
else
  echo "'solcon-master.zip' not found, downloading"
  curl https://github.com/NSO-developer/nfvo-converter-tosca-sol6/archive/master.zip -L -0 -o solcon-master.zip
fi

echo "Extracting archive..."
# Check for unzip
if hash unzip 2>/dev/null; then
    unzip solcon-master.zip

    echo "Removing 'solcon-master.zip'"
    rm solcon-master.zip
else
    echo "unzip not found, please unzip manually."
    exit
fi
